"""
Settings manager for Foxden dashboard.
Persists application-level settings (RAM, selected JDK, target JAR, Discord webhook, show IP)
in foxden_settings.json.
"""

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_SETTINGS = {
    "min_ram_gb": 2,
    "max_ram_gb": 4,
    "target_jar": "server.jar",
    "installed_version": "26.3",
    "selected_jdk": "auto",
    "discord_webhook_url": "",
    "discord_show_ip": True,
    "public_ip_alias": "",
}


class SettingsManager:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.settings_file = self.base_dir / "foxden_settings.json"
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        if not self.settings_file.exists():
            self._data = dict(DEFAULT_SETTINGS)
            return self._data

        try:
            content = self.settings_file.read_text(encoding="utf-8")
            loaded = json.loads(content)
            self._data = dict(DEFAULT_SETTINGS)
            self._data.update(loaded)
        except Exception:
            self._data = dict(DEFAULT_SETTINGS)

        return self._data

    def save(self) -> None:
        try:
            self.settings_file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def update(self, updates: Dict[str, Any]) -> None:
        self._data.update(updates)
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)
