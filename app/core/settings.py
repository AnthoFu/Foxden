"""
Gestor de configuraciones y ajustes de Foxden.
Guarda los ajustes a nivel de aplicación (RAM, JDK seleccionado, JAR de destino,
webhook de Discord, mostrar IP) en foxden_settings.json.
"""

import json
from pathlib import Path
from typing import Any, Dict


# Ajustes predeterminados para la primera inicialización
AJUSTES_PREDETERMINADOS = {
    "min_ram_gb": 2,
    "max_ram_gb": 4,
    "target_jar": "server.jar",
    "installed_version": "26.3",
    "installed_engine": "vanilla",
    "selected_jdk": "auto",
    "discord_webhook_url": "",
    "discord_show_ip": True,
    "public_ip_alias": "",
}

# Alias para compatibilidad
DEFAULT_SETTINGS = AJUSTES_PREDETERMINADOS


class SettingsManager:
    """Administra la persistencia en disco del archivo foxden_settings.json."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.settings_file = self.base_dir / "foxden_settings.json"
        self._data: Dict[str, Any] = {}
        self.cargar()

    def cargar(self) -> Dict[str, Any]:
        """Carga los ajustes desde el archivo JSON si existe."""
        if not self.settings_file.exists():
            self._data = dict(AJUSTES_PREDETERMINADOS)
            return self._data

        try:
            contenido = self.settings_file.read_text(encoding="utf-8")
            cargado = json.loads(contenido)
            self._data = dict(AJUSTES_PREDETERMINADOS)
            self._data.update(cargado)
        except Exception:
            self._data = dict(AJUSTES_PREDETERMINADOS)

        return self._data

    def guardar(self) -> None:
        """Escribe los ajustes actuales al disco en formato JSON formateado."""
        try:
            self.settings_file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    def obtener(self, clave: str, predeterminado: Any = None) -> Any:
        """Obtiene un valor de configuración por su clave."""
        return self._data.get(clave, predeterminado)

    def establecer(self, clave: str, valor: Any) -> None:
        """Establece un valor de configuración y lo guarda en disco."""
        self._data[clave] = valor
        self.guardar()

    def actualizar(self, actualizaciones: Dict[str, Any]) -> None:
        """Actualiza múltiples valores de configuración y los guarda en disco."""
        self._data.update(actualizaciones)
        self.guardar()

    def a_diccionario(self) -> Dict[str, Any]:
        """Devuelve una copia del diccionario completo de ajustes."""
        return dict(self._data)

    # Alias en inglés para compatibilidad
    load = cargar
    save = guardar
    get = obtener
    set = establecer
    update = actualizar
    to_dict = a_diccionario
