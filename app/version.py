"""
Versión del sistema Foxden.
Fuente única de la verdad para la versión de la aplicación.
Lee la versión dinámicamente desde version.json en la raíz del repositorio.
"""

import json
from pathlib import Path

_archivo_version = Path(__file__).resolve().parent.parent / "version.json"

try:
    if _archivo_version.exists():
        _datos = json.loads(_archivo_version.read_text(encoding="utf-8"))
        __version__ = _datos.get("version", "1.0.0")
    else:
        __version__ = "1.0.0"
except Exception:
    __version__ = "1.0.0"

VERSION = __version__
