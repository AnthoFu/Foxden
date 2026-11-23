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
        candidatos: List[Path] = [
            Path("/usr/lib/jvm/java-25-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-21-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-17-temurin-jdk/bin/java"),
            Path("/usr/bin/java"),
        ]

        # 1. Escanear subdirectorios dentro de /usr/lib/jvm
        dir_jvm = Path("/usr/lib/jvm")
        if dir_jvm.exists():
            for p in dir_jvm.glob("*/bin/java"):
                candidatos.append(p)

        # 2. Escanear SDKMAN en rutas de sistema y usuario (típico en devcontainers/Codespaces)
        rutas_sdkman = [
            Path("/usr/local/sdkman/candidates/java"),
            Path.home() / ".sdkman/candidates/java",
        ]
        for dir_sdk in rutas_sdkman:
            if dir_sdk.exists():
                for p in dir_sdk.glob("*/bin/java"):
                    candidatos.append(p)

        # 3. Escanear ASDF
        dir_asdf = Path.home() / ".asdf/installs/java"
        if dir_asdf.exists():
            for p in dir_asdf.glob("*/bin/java"):
                candidatos.append(p)

        # 4. Escanear JAVA_HOME si está definido en el entorno
        java_home_env = os.environ.get("JAVA_HOME")
        if java_home_env:
            candidatos.append(Path(java_home_env) / "bin" / "java")

        encontrados = []
        rutas_vistas = set()

        for ruta_bin in candidatos:
            try:
                resuelta = ruta_bin.resolve()
            except Exception:
                continue

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

        # Requerimientos de Java según versión oficial de Minecraft:
        # Minecraft 26.x (snapshots futuros) -> Java 25
        # Minecraft 1.20.5 - 1.21.x -> Java 21 (LTS)
        # Minecraft 1.18 - 1.20.4 -> Java 17 (LTS)
        # Minecraft 1.17.x -> Java 17 (o 16)
        # Minecraft < 1.17 -> Java 8 (o 11/17 según modloader)
        mayor_requerido = 17
        if version_mc:
            v_limpia = version_mc.strip().lower()
            if v_limpia.startswith("26"):
                mayor_requerido = 25
            elif v_limpia.startswith("1.21") or v_limpia.startswith("21.") or v_limpia.startswith("1.20.5") or v_limpia.startswith("1.20.6"):
                mayor_requerido = 21
            elif v_limpia.startswith("1.18") or v_limpia.startswith("1.19") or v_limpia.startswith("1.20") or v_limpia.startswith("20."):
                mayor_requerido = 17
            elif v_limpia.startswith("1.17"):
                mayor_requerido = 17
            elif any(v_limpia.startswith(pfx) for pfx in ["1.7", "1.8", "1.12", "1.16"]):
                mayor_requerido = 8

        # 1. Prioridad: Coincidencia exacta de versión
        for jdk in jdks:
            if jdk["major"] == mayor_requerido:
                return jdk

        # 2. Si no hay coincidencia exacta:
        # Filtrar versiones experimentales no probadas (> 25, como Java 27) que rompen ModLauncher
        candidatos_seguros = [j for j in jdks if j["major"] <= 25] or jdks

        # Seleccionar el JDK más cercano en versión al requerido
        candidatos_seguros.sort(key=lambda x: abs(x["major"] - mayor_requerido))
        return candidatos_seguros[0]

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
