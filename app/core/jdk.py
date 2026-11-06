"""
Módulo de detección y administración de versiones de JDK para Minecraft.
Encuentra entornos Java instalados en el sistema y selecciona el adecuado
según los requerimientos de la versión de Minecraft.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class JdkManager:
    """Administrador para escanear y asignar entornos de ejecución Java (JDK/JRE)."""

    def __init__(self) -> None:
        self._cached_jdks: Optional[List[Dict]] = None

    def listar_jdks_instalados(self) -> List[Dict]:
        """Escanea el sistema en busca de entornos Java instalados."""
        candidatos = [
            Path("/usr/lib/jvm/java-25-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-21-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-17-temurin-jdk/bin/java"),
            Path("/usr/bin/java"),
        ]

        # Escanear subdirectorios dentro de /usr/lib/jvm
        dir_jvm = Path("/usr/lib/jvm")
        if dir_jvm.exists():
            for p in dir_jvm.glob("*/bin/java"):
                if p not in candidatos:
                    candidatos.append(p)

        encontrados = []
        rutas_vistas = set()

        for ruta_bin in candidatos:
            resuelta = ruta_bin.resolve()
            if not resuelta.exists() or str(resuelta) in rutas_vistas:
                continue
            rutas_vistas.add(str(resuelta))

            try:
                salida = subprocess.check_output([str(resuelta), "-version"], stderr=subprocess.STDOUT, text=True)
                m = re.search(r'version "(?:1\.)?(\d+)', salida)
                if m:
                    version_mayor = int(m.group(1))
                    primera_linea = salida.splitlines()[0] if salida.splitlines() else f"Java {version_mayor}"
                    encontrados.append({
                        "major": version_mayor,
                        "path": str(resuelta),
                        "name": f"Java {version_mayor} ({primera_linea.split('(')[0].strip()})",
                        "home": str(resuelta.parent.parent),
                    })
            except Exception:
                pass

        # Ordenar descendente por versión mayor
        encontrados.sort(key=lambda x: x["major"], reverse=True)
        return encontrados

    def obtener_mejor_jdk_para_version(self, version_mc: Optional[str] = None) -> Dict:
        """Encuentra el mejor JDK instalado según la versión de Minecraft especificada."""
        jdks = self.listar_jdks_instalados()
        if not jdks:
            return {"major": 0, "path": "java", "name": "Java predeterminado del sistema", "home": ""}

        # Requerimientos de Java según versión de Minecraft:
        # Minecraft 26.x requiere Java 25 (class file 69.0)
        # Minecraft 1.20.5 - 1.21.x requiere Java 21 (class file 65.0)
        # Minecraft 1.18 - 1.20.4 requiere Java 17 (class file 61.0)
        mayor_requerido = 17
        if version_mc:
            v_limpia = version_mc.strip()
            if v_limpia.startswith("26"):
                mayor_requerido = 25
            elif v_limpia.startswith("1.21") or v_limpia.startswith("1.20.5") or v_limpia.startswith("1.20.6"):
                mayor_requerido = 21

        # Buscar coincidencia exacta de versión
        for jdk in jdks:
            if jdk["major"] == mayor_requerido:
                return jdk

        # Si hay una versión superior disponible, usarla
        for jdk in jdks:
            if jdk["major"] >= mayor_requerido:
                return jdk

        # Fallback al JDK más alto disponible
        return jdks[0]

    def construir_entorno_para_jdk(self, info_jdk: Dict) -> dict:
        """Genera un diccionario de variables de entorno con JAVA_HOME y PATH adaptados al JDK."""
        entorno = os.environ.copy()
        home = info_jdk.get("home")
        if home and Path(home).exists():
            entorno["JAVA_HOME"] = home
            dir_bin = str(Path(home) / "bin")
            entorno["PATH"] = f"{dir_bin}:{entorno.get('PATH', '')}"
        return entorno

    # Alias en inglés para compatibilidad
    list_installed_jdks = listar_jdks_instalados
    get_best_jdk_for_version = obtener_mejor_jdk_para_version
    build_env_for_jdk = construir_entorno_para_jdk
