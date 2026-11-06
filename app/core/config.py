"""
Módulo de gestión de configuración para el servidor de Minecraft.
Maneja la lectura y actualización de server.properties, eula.txt y parámetros JVM.
"""

from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """Administrador de archivos de configuración del servidor de Minecraft."""

    def __init__(self, server_dir: Path) -> None:
        self.server_dir = Path(server_dir).resolve()

    @property
    def ruta_propiedades(self) -> Path:
        """Ruta al archivo server.properties."""
        return self.server_dir / "server.properties"

    # Alias de compatibilidad
    properties_path = ruta_propiedades

    @property
    def ruta_eula(self) -> Path:
        """Ruta al archivo eula.txt."""
        return self.server_dir / "eula.txt"

    # Alias de compatibilidad
    eula_path = ruta_eula

    def asegurar_eula_aceptado(self) -> None:
        """Asegura que el archivo eula.txt exista con eula=true para permitir iniciar."""
        self.server_dir.mkdir(parents=True, exist_ok=True)
        self.ruta_eula.write_text("eula=true\n", encoding="utf-8")

    def leer_propiedades(self) -> Dict[str, str]:
        """Lee el archivo server.properties y lo devuelve como diccionario clave-valor."""
        if not self.ruta_propiedades.exists():
            return {}

        propiedades: Dict[str, str] = {}
        for linea in self.ruta_propiedades.read_text(encoding="utf-8", errors="replace").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" in linea:
                clave, valor = linea.split("=", 1)
                propiedades[clave.strip()] = valor.strip()
        return propiedades

    def actualizar_propiedades(self, actualizaciones: Dict[str, str]) -> None:
        """Actualiza claves específicas en server.properties conservando comentarios y claves no modificadas."""
        if not self.ruta_propiedades.exists():
            # Crear archivo nuevo de propiedades con encabezado
            lineas = ["# Propiedades del servidor de Minecraft", "# Generado automáticamente por Foxden"]
            for k, v in actualizaciones.items():
                lineas.append(f"{k}={v}")
            self.ruta_propiedades.write_text("\n".join(lineas) + "\n", encoding="utf-8")
            return

        lineas = self.ruta_propiedades.read_text(encoding="utf-8", errors="replace").splitlines()
        claves_actualizadas = set()
        nuevas_lineas = []

        for linea in lineas:
            limpia = linea.strip()
            if limpia and not limpia.startswith("#") and "=" in limpia:
                clave, _ = limpia.split("=", 1)
                clave = clave.strip()
                if clave in actualizaciones:
                    nuevas_lineas.append(f"{clave}={actualizaciones[clave]}")
                    claves_actualizadas.add(clave)
                    continue
            nuevas_lineas.append(linea)

        # Agregar claves nuevas que no estaban en el archivo original
        for k, v in actualizaciones.items():
            if k not in claves_actualizadas:
                nuevas_lineas.append(f"{k}={v}")

        self.ruta_propiedades.write_text("\n".join(nuevas_lineas) + "\n", encoding="utf-8")

    def obtener_resumen_ajustes(self) -> dict:
        """Devuelve los ajustes más comunes en formato amigable para el panel."""
        props = self.leer_propiedades()
        return {
            "server_port": int(props.get("server-port", 25565)),
            "motd": props.get("motd", "A Minecraft Server"),
            "max_players": int(props.get("max-players", 20)),
            "difficulty": props.get("difficulty", "easy"),
            "gamemode": props.get("gamemode", "survival"),
            "online_mode": props.get("online-mode", "true").lower() == "true",
            "pvp": props.get("pvp", "true").lower() == "true",
            "white_list": props.get("white-list", "false").lower() == "true",
            "view_distance": int(props.get("view-distance", 10)),
            "level_seed": props.get("level-seed", ""),
        }

    # Alias en inglés para compatibilidad
    ensure_eula_accepted = asegurar_eula_aceptado
    read_properties = leer_propiedades
    update_properties = actualizar_propiedades
    get_summary_settings = obtener_resumen_ajustes
