"""
Gestor de Mods y Modpacks para Foxden.
Administra el ciclo de vida de los mods en servidor_minecraft/mods/:
listado, subida de .jar, descompresión de modpacks .zip, activación/desactivación
y eliminación segura.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional
import zipfile


class ModManager:
    """Administrador de archivos de mods y modpacks locales."""

    def __init__(self, server_dir: Path) -> None:
        self.server_dir = Path(server_dir).resolve()
        self.mods_dir = self.server_dir / "mods"
        self.config_dir = self.server_dir / "config"
        self._asegurar_directorios()

    def _asegurar_directorios(self) -> None:
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _extraer_metadatos_jar(self, archivo_path: Path) -> Dict[str, str]:
        """Intenta leer la información del mod desde los manifiestos estándar."""
        metadatos = {
            "name": archivo_path.stem.replace(".jar", ""),
            "version": "",
            "description": "",
            "loader": "unknown",
        }
        if not archivo_path.exists() or archivo_path.stat().st_size == 0:
            return metadatos

        try:
            with zipfile.ZipFile(archivo_path, "r") as z:
                nombres = set(z.namelist())

                # 1. Fabric mod
                if "fabric.mod.json" in nombres:
                    try:
                        raw = z.read("fabric.mod.json").decode("utf-8", errors="ignore")
                        data = json.loads(raw)
                        metadatos["name"] = data.get("name", metadatos["name"])
                        metadatos["version"] = str(data.get("version", ""))
                        metadatos["description"] = data.get("description", "")
                        metadatos["loader"] = "fabric"
                        return metadatos
                    except Exception:
                        pass

                # 2. NeoForge / Forge mods.toml
                toml_candidatos = [
                    "META-INF/neoforge.mods.toml",
                    "META-INF/mods.toml",
                ]
                for toml_path in toml_candidatos:
                    if toml_path in nombres:
                        try:
                            raw = z.read(toml_path).decode("utf-8", errors="ignore")
                            match_name = re.search(r'displayName\s*=\s*["\']([^"\']+)["\']', raw)
                            match_ver = re.search(r'version\s*=\s*["\']([^"\']+)["\']', raw)
                            match_desc = re.search(r'description\s*=\s*["\']([^"\']+)["\']', raw)

                            if match_name:
                                metadatos["name"] = match_name.group(1)
                            if match_ver:
                                metadatos["version"] = match_ver.group(1)
                            if match_desc:
                                metadatos["description"] = match_desc.group(1)
                            metadatos["loader"] = "neoforge" if "neoforge" in toml_path else "forge"
                            return metadatos
                        except Exception:
                            pass

                # 3. Forge clásico mcmod.info
                if "mcmod.info" in nombres:
                    try:
                        raw = z.read("mcmod.info").decode("utf-8", errors="ignore")
                        data = json.loads(raw)
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]
                        if isinstance(data, dict):
                            metadatos["name"] = data.get("name", metadatos["name"])
                            metadatos["version"] = str(data.get("version", ""))
                            metadatos["description"] = data.get("description", "")
                            metadatos["loader"] = "forge"
                            return metadatos
                    except Exception:
                        pass
        except Exception:
            pass

        return metadatos

    def listar_mods(self) -> List[Dict[str, Any]]:
        """Devuelve la lista detallada de mods encontrados en servidor_minecraft/mods/."""
        self._asegurar_directorios()
        resultado = []

        for elemento in sorted(self.mods_dir.iterdir()):
            if not elemento.is_file():
                continue
            nombre = elemento.name

            es_activo = nombre.endswith(".jar")
            es_desactivado = nombre.endswith(".jar.disabled")

            if not es_activo and not es_desactivado:
                continue

            stat = elemento.stat()
            meta = self._extraer_metadatos_jar(elemento)

            resultado.append({
                "filename": nombre,
                "name": meta["name"],
                "version": meta["version"],
                "description": meta["description"],
                "loader": meta["loader"],
                "enabled": es_activo,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            })

        return resultado

    def alternar_estado(self, nombre_archivo: str, activar: bool) -> Dict[str, Any]:
        """Activa o desactiva un mod renombrándolo (.jar <-> .jar.disabled)."""
        nombre_limpio = Path(nombre_archivo).name
        if nombre_limpio != nombre_archivo:
            raise ValueError("Nombre de archivo inválido.")

        archivo_origen = self.mods_dir / nombre_limpio
        if not archivo_origen.exists():
            raise FileNotFoundError(f"El archivo {nombre_limpio} no existe.")

        if activar:
            if not nombre_limpio.endswith(".disabled"):
                destino = archivo_origen
                nuevo_nombre = nombre_limpio
            else:
                nuevo_nombre = nombre_limpio[:-9]  # Quita '.disabled'
                destino = self.mods_dir / nuevo_nombre
                archivo_origen.rename(destino)
        else:
            if nombre_limpio.endswith(".disabled"):
                destino = archivo_origen
                nuevo_nombre = nombre_limpio
            else:
                nuevo_nombre = f"{nombre_limpio}.disabled"
                destino = self.mods_dir / nuevo_nombre
                archivo_origen.rename(destino)

        stat = destino.stat()
        meta = self._extraer_metadatos_jar(destino)
        return {
            "filename": nuevo_nombre,
            "name": meta["name"],
            "version": meta["version"],
            "description": meta["description"],
            "loader": meta["loader"],
            "enabled": nuevo_nombre.endswith(".jar"),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        }

    def eliminar_mod(self, nombre_archivo: str) -> bool:
        """Elimina un mod de disco de forma segura."""
        nombre_limpio = Path(nombre_archivo).name
        if nombre_limpio != nombre_archivo:
            raise ValueError("Nombre de archivo inválido.")

        archivo = self.mods_dir / nombre_limpio
        if archivo.is_file():
            archivo.unlink()
            return True
        return False

    def instalar_archivo(self, contenido: bytes, nombre_archivo: str) -> Dict[str, Any]:
        """
        Instala un archivo en el servidor.
        Si es .jar, lo guarda directamente en mods/.
        Si es .zip (modpack), extrae los .jar a mods/ y las configuraciones a config/.
        """
        nombre_limpio = Path(nombre_archivo).name
        self._asegurar_directorios()

        if nombre_limpio.endswith(".jar"):
            destino = self.mods_dir / nombre_limpio
            destino.write_bytes(contenido)
            meta = self._extraer_metadatos_jar(destino)
            return {
                "type": "jar",
                "installed_files": [nombre_limpio],
                "message": f"Mod {meta['name']} instalado correctamente.",
            }

        if nombre_limpio.endswith(".zip"):
            import io
            instalados = []
            configs_extraidas = 0

            try:
                with zipfile.ZipFile(io.BytesIO(contenido)) as z:
                    for miembro in z.infolist():
                        if miembro.is_dir():
                            continue

                        partes = Path(miembro.filename).parts
                        nombre_miembro = Path(miembro.filename).name

                        # 1. Archivos .jar dentro de mods/ o en cualquier subcarpeta
                        if nombre_miembro.endswith(".jar"):
                            destino = self.mods_dir / nombre_miembro
                            with z.open(miembro) as src, open(destino, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            instalados.append(nombre_miembro)

                        # 2. Archivos de configuración en config/ u overrides/config/
                        elif "config" in partes:
                            idx = partes.index("config")
                            subruta = Path(*partes[idx + 1:])
                            if subruta.name:
                                destino_conf = self.config_dir / subruta
                                destino_conf.parent.mkdir(parents=True, exist_ok=True)
                                with z.open(miembro) as src, open(destino_conf, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                                configs_extraidas += 1

                return {
                    "type": "zip_modpack",
                    "installed_files": instalados,
                    "configs_count": configs_extraidas,
                    "message": f"Modpack descomprimido: {len(instalados)} mods y {configs_extraidas} configuraciones instaladas.",
                }
            except Exception as e:
                raise ValueError(f"El archivo ZIP está dañado o no es un modpack válido: {e}")

        raise ValueError("Formato no admitido. Solo se admiten archivos .jar o .zip de modpacks.")
