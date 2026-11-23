"""
Instalador de servidores y descargador de archivos JAR.
Descarga compilaciones oficiales desde Mojang (Vanilla), Fabric (Mods),
Minecraft Forge y NeoForge.
"""

import asyncio
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import httpx

from app.core.jdk import JdkManager


class ServerInstaller:
    """Instalador automatizado de servidores de Minecraft y cargadores de mods."""

    URL_MANIFIESTO_MOJANG = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    URL_META_FABRIC = "https://meta.fabricmc.net/v2/versions"
    URL_PROMOS_FORGE = "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
    URL_MAVEN_FORGE = "https://maven.minecraftforge.net/net/minecraftforge/forge"
    URL_MAVEN_META_NEOFORGE = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
    URL_MAVEN_NEOFORGE = "https://maven.neoforged.net/releases/net/neoforged/neoforge"
    URL_NEOFORGE_LEGADO_1201 = "https://maven.neoforged.net/releases/net/neoforged/forge"

    # Alias para compatibilidad
    MOJANG_MANIFEST_URL = URL_MANIFIESTO_MOJANG
    FABRIC_META_URL = URL_META_FABRIC
    FORGE_PROMOS_URL = URL_PROMOS_FORGE
    FORGE_MAVEN_BASE = URL_MAVEN_FORGE
    NEOFORGE_MAVEN_META = URL_MAVEN_META_NEOFORGE
    NEOFORGE_MAVEN_BASE = URL_MAVEN_NEOFORGE
    NEOFORGE_LEGACY_1201_BASE = URL_NEOFORGE_LEGADO_1201

    def __init__(self, server_dir: Path, jdk_manager: Optional[JdkManager] = None) -> None:
        self.server_dir = Path(server_dir).resolve()
        self.jdk_manager = jdk_manager or JdkManager()
        self._mojang_manifest_cache: Optional[dict] = None
        self._forge_promos_cache: Optional[dict] = None
        self._neoforge_manifest_cache: Optional[Dict[str, str]] = None
        self._neoforge_builds_cache: Optional[Dict[str, List[str]]] = None

    @staticmethod
    def _clave_version_semver(v: str) -> List[int]:
        partes = []
        for p in re.split(r"[.\-]", v):
            try:
                partes.append(int(p))
            except ValueError:
                partes.append(0)
        return partes

    async def obtener_manifiesto_mojang(self) -> dict:
        """Obtiene el manifiesto oficial de versiones publicado por Mojang."""
        if self._mojang_manifest_cache is None:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                res = await cliente.get(self.URL_MANIFIESTO_MOJANG)
                res.raise_for_status()
                self._mojang_manifest_cache = res.json()
        return self._mojang_manifest_cache

    async def obtener_promociones_forge(self) -> dict:
        """Obtiene las promociones y versiones recomendadas de Minecraft Forge."""
        if self._forge_promos_cache is None:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                res = await cliente.get(self.URL_PROMOS_FORGE)
                res.raise_for_status()
                self._forge_promos_cache = res.json()
        return self._forge_promos_cache

    async def obtener_manifiesto_neoforge(self) -> Dict[str, str]:
        """Obtiene y mapea las versiones estables de NeoForge para cada versión de Minecraft."""
        if self._neoforge_manifest_cache is not None:
            return self._neoforge_manifest_cache

        mapeo: Dict[str, str] = {}
        builds_map: Dict[str, List[str]] = {}

        # 1.20.1 se aloja bajo net.neoforged:forge
        builds_map["1.20.1"] = ["1.20.1-47.1.106", "1.20.1-47.1.105", "1.20.1-47.1.104"]
        mapeo["1.20.1"] = "1.20.1-47.1.106"

        try:
            async with httpx.AsyncClient(timeout=10.0) as cliente:
                res = await cliente.get(self.URL_MAVEN_META_NEOFORGE)
                if res.status_code == 200:
                    raiz = ET.fromstring(res.text)
                    versiones_crudas = [v.text for v in raiz.findall(".//version") if v.text]
                    for v in versiones_crudas:
                        m = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?(-.*)?$", v)
                        if not m:
                            continue
                        mayor = int(m.group(1))
                        menor = int(m.group(2))
                        etiqueta = (m.group(5) or "").lower()

                        if "alpha" in etiqueta or "snapshot" in etiqueta or "pre" in etiqueta:
                            continue

                        if mayor in (20, 21):
                            mc_ver = f"1.{mayor}.{menor}" if menor > 0 else f"1.{mayor}"
                        elif mayor >= 26:
                            mc_ver = f"{mayor}.{menor}"
                        else:
                            continue

                        builds_map.setdefault(mc_ver, []).append(v)

                    for mc, b_list in builds_map.items():
                        ordenadas = sorted(list(set(b_list)), key=self._clave_version_semver, reverse=True)
                        builds_map[mc] = ordenadas
                        mapeo[mc] = ordenadas[0]

        except Exception:
            pass

        # Catálogo de respaldo si Maven no responde
        if not mapeo or len(mapeo) <= 1:
            respaldo = {
                "26.3": ["26.3.0.101"],
                "26.2": ["26.2.0.93"],
                "26.1": ["26.1.2.126"],
                "1.21.4": ["21.4.161", "21.4.160"],
                "1.21.3": ["21.3.100"],
                "1.21.1": ["21.1.267", "21.1.266", "21.1.265", "21.1.218", "21.1.0"],
                "1.21": ["21.0.167"],
                "1.20.6": ["20.6.144"],
                "1.20.4": ["20.4.253"],
                "1.20.2": ["20.2.93"],
                "1.20.1": ["1.20.1-47.1.106", "1.20.1-47.1.105"],
            }
            for k, lista in respaldo.items():
                builds_map.setdefault(k, lista)
                mapeo.setdefault(k, lista[0])

        self._neoforge_manifest_cache = mapeo
        self._neoforge_builds_cache = builds_map
        return self._neoforge_manifest_cache

    async def obtener_compilaciones_neoforge(self, mc_version: str) -> List[str]:
        """Obtiene todas las compilaciones disponibles de NeoForge para una versión de Minecraft."""
        if self._neoforge_builds_cache is None:
            await self.obtener_manifiesto_neoforge()
        limpia = mc_version.strip()
        return self._neoforge_builds_cache.get(limpia, []) if self._neoforge_builds_cache else []

    async def obtener_versiones(self, tipo_servidor: str = "vanilla", incluir_snapshots: bool = False) -> List[str]:
        """Obtiene las versiones disponibles según el tipo de servidor (vanilla, fabric, forge, neoforge)."""
        tipo_servidor = tipo_servidor.lower()
        try:
            if tipo_servidor == "vanilla":
                manifiesto = await self.obtener_manifiesto_mojang()
                versiones = [
                    v["id"]
                    for v in manifiesto.get("versions", [])
                    if v.get("type") == "release" or (incluir_snapshots and v.get("type") == "snapshot")
                ]
                return versiones

            elif tipo_servidor == "neoforge":
                mapeo = await self.obtener_manifiesto_neoforge()

                def clave_orden(v: str):
                    partes = []
                    for p in v.split("."):
                        try:
                            partes.append(int(p))
                        except ValueError:
                            partes.append(0)
                    return partes

                return sorted(mapeo.keys(), key=clave_orden, reverse=True)

            elif tipo_servidor == "fabric":
                async with httpx.AsyncClient(timeout=10.0) as cliente:
                    res = await cliente.get(f"{self.URL_META_FABRIC}/game")
                    if res.status_code == 200:
                        versiones = [v["version"] for v in res.json() if v.get("stable")]
                        return versiones

            elif tipo_servidor == "forge":
                datos = await self.obtener_promociones_forge()
                promos = datos.get("promos", {})
                versiones_crudas = set()
                for k in promos.keys():
                    versiones_crudas.add(k.replace("-latest", "").replace("-recommended", ""))

                def clave_orden_forge(v: str):
                    partes = []
                    for p in v.split("."):
                        try:
                            partes.append(int(p))
                        except ValueError:
                            partes.append(0)
                    return partes

                return sorted(versiones_crudas, key=clave_orden_forge, reverse=True)

        except Exception:
            pass

        return ["26.3", "26.2", "26.1", "1.21.4", "1.21.3", "1.21.1", "1.20.4", "1.20.1", "1.19.4", "1.18.2", "1.16.5", "1.12.2"]

    async def descargar_servidor(self, tipo_servidor: str, version: str, build: Optional[str] = None) -> Path:
        """Descarga e instala el ejecutable oficial del servidor de Minecraft seleccionado."""
        self.server_dir.mkdir(parents=True, exist_ok=True)
        tipo_servidor = tipo_servidor.lower()
        ruta_destino = self.server_dir / "server.jar"

        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as cliente:
            if tipo_servidor == "vanilla":
                # Eliminar run.sh previo si existía de una instalación de Forge/NeoForge
                run_sh = self.server_dir / "run.sh"
                if run_sh.exists():
                    try:
                        run_sh.unlink()
                    except Exception:
                        pass

                manifiesto = await self.obtener_manifiesto_mojang()
                ver_objetivo = next((v for v in manifiesto.get("versions", []) if v["id"] == version), None)
                if not ver_objetivo:
                    raise RuntimeError(f"Versión {version} no encontrada en el manifiesto de Mojang.")

                res_meta = await cliente.get(ver_objetivo["url"])
                res_meta.raise_for_status()
                meta = res_meta.json()
                descarga_servidor = meta.get("downloads", {}).get("server")
                if not descarga_servidor or "url" not in descarga_servidor:
                    raise RuntimeError(f"No hay jar de servidor disponible para vanilla {version}")

                async with cliente.stream("GET", descarga_servidor["url"]) as respuesta:
                    respuesta.raise_for_status()
                    with open(ruta_destino, "wb") as f:
                        async for bloque in respuesta.aiter_bytes(chunk_size=65536):
                            f.write(bloque)
                return ruta_destino

            elif tipo_servidor == "fabric":
                # Eliminar run.sh previo si existía de una instalación de Forge/NeoForge
                run_sh = self.server_dir / "run.sh"
                if run_sh.exists():
                    try:
                        run_sh.unlink()
                    except Exception:
                        pass

                res_loader = await cliente.get(f"{self.URL_META_FABRIC}/loader")
                res_loader.raise_for_status()
                version_loader = res_loader.json()[0]["version"]

                res_instalador = await cliente.get(f"{self.URL_META_FABRIC}/installer")
                res_instalador.raise_for_status()
                version_instalador = res_instalador.json()[0]["version"]

                url_descarga = f"{self.URL_META_FABRIC}/loader/{version}/{version_loader}/{version_instalador}/server/jar"
                async with cliente.stream("GET", url_descarga) as respuesta:
                    respuesta.raise_for_status()
                    with open(ruta_destino, "wb") as f:
                        async for bloque in respuesta.aiter_bytes(chunk_size=65536):
                            f.write(bloque)
                return ruta_destino

            elif tipo_servidor == "forge":
                datos = await self.obtener_promociones_forge()
                promos = datos.get("promos", {})
                ver_forge = promos.get(f"{version}-recommended") or promos.get(f"{version}-latest")
                if not ver_forge:
                    raise RuntimeError(f"No se encontró compilación de Forge para Minecraft {version}")

                nombre_archivo = f"forge-{version}-{ver_forge}-installer.jar"
                url_instalador = f"{self.URL_MAVEN_FORGE}/{version}-{ver_forge}/{nombre_archivo}"
                ruta_instalador = self.server_dir / "forge-installer.jar"

                async with cliente.stream("GET", url_instalador) as respuesta:
                    respuesta.raise_for_status()
                    with open(ruta_instalador, "wb") as f:
                        async for bloque in respuesta.aiter_bytes(chunk_size=65536):
                            f.write(bloque)

                info_jdk = self.jdk_manager.obtener_mejor_jdk_para_version(version)
                bin_java = info_jdk.get("path", "java")
                entorno = self.jdk_manager.construir_entorno_para_jdk(info_jdk)

                proceso_instalador = await asyncio.create_subprocess_exec(
                    bin_java,
                    "-jar",
                    "forge-installer.jar",
                    "--installServer",
                    cwd=str(self.server_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=entorno,
                )
                await proceso_instalador.communicate()

                if ruta_instalador.exists():
                    ruta_instalador.unlink()

                run_sh = self.server_dir / "run.sh"
                if run_sh.exists():
                    os.chmod(str(run_sh), 0o755)
                    return run_sh

                for jar in self.server_dir.glob("forge-*.jar"):
                    if not jar.name.endswith("installer.jar"):
                        return jar

                return ruta_destino

            elif tipo_servidor == "neoforge":
                mapeo = await self.obtener_manifiesto_neoforge()
                ver_compilacion = (build.strip() if build and build.strip() else None) or mapeo.get(version) or version
                ruta_instalador = self.server_dir / "neoforge-installer.jar"

                if version == "1.20.1" or "1.20.1" in ver_compilacion:
                    url_instalador = f"{self.URL_NEOFORGE_LEGADO_1201}/{ver_compilacion}/forge-{ver_compilacion}-installer.jar"
                else:
                    url_instalador = f"{self.URL_MAVEN_NEOFORGE}/{ver_compilacion}/neoforge-{ver_compilacion}-installer.jar"

                async with cliente.stream("GET", url_instalador) as respuesta:
                    respuesta.raise_for_status()
                    with open(ruta_instalador, "wb") as f:
                        async for bloque in respuesta.aiter_bytes(chunk_size=65536):
                            f.write(bloque)

                info_jdk = self.jdk_manager.obtener_mejor_jdk_para_version(version)
                bin_java = info_jdk.get("path", "java")
                entorno = self.jdk_manager.construir_entorno_para_jdk(info_jdk)

                proceso_instalador = await asyncio.create_subprocess_exec(
                    bin_java,
                    "-jar",
                    "neoforge-installer.jar",
                    "--installServer",
                    cwd=str(self.server_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=entorno,
                )
                await proceso_instalador.communicate()

                if ruta_instalador.exists():
                    ruta_instalador.unlink()

                run_sh = self.server_dir / "run.sh"
                if run_sh.exists():
                    os.chmod(str(run_sh), 0o755)
                    return run_sh

                for jar in self.server_dir.glob("neoforge-*.jar"):
                    if not jar.name.endswith("installer.jar"):
                        return jar

                for jar in self.server_dir.glob("forge-*.jar"):
                    if not jar.name.endswith("installer.jar"):
                        return jar

                return ruta_destino

            else:
                raise ValueError(f"Tipo de servidor no soportado: {tipo_servidor}")

    def esta_servidor_instalado(self) -> bool:
        """Comprueba si existe un ejecutable o archivo JAR de servidor instalado en el directorio."""
        if not self.server_dir.exists():
            return False
        if (self.server_dir / "run.sh").exists():
            return True
        for jar in self.server_dir.glob("*.jar"):
            if not jar.name.endswith("installer.jar"):
                return True
        return False

    def listar_jars_instalados(self) -> List[str]:
        """Lista los archivos JAR o scripts de ejecución presentes en el directorio del servidor."""
        if not self.server_dir.exists():
            return []
        archivos = []
        for p in self.server_dir.glob("*.jar"):
            archivos.append(p.name)
        for p in self.server_dir.glob("run.sh"):
            archivos.append(p.name)
        return sorted(archivos)

    # Alias en inglés para compatibilidad
    get_mojang_manifest = obtener_manifiesto_mojang
    get_forge_promos = obtener_promociones_forge
    get_neoforge_manifest = obtener_manifiesto_neoforge
    get_neoforge_builds = obtener_compilaciones_neoforge
    get_versions = obtener_versiones
    download_server = descargar_servidor
    is_server_installed = esta_servidor_instalado
    list_installed_jars = listar_jars_instalados
