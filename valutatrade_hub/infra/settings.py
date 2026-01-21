import json
import os
from typing import Any


class SettingsLoader:
    """
    Singleton для загрузки и хранения конфигурации проекта.

    Реализация через __new__:
    - простой и читаемый вариант
    - гарантирует один экземпляр во всём приложении
    """

    _instance = None

    def __new__(cls, config_path: str | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(config_path)
        return cls._instance

    def _init(self, config_path: str | None):
        self._config_path = config_path or self._default_config_path()
        self._config: dict[str, Any] = {}
        self.reload()

    @staticmethod
    def _default_config_path() -> str:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )
        return os.path.join(base_dir, "data", "config.json")

    def reload(self) -> None:
        """Перезагрузка конфигурации с диска"""
        if os.path.exists(self._config_path):
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения конфигурации"""
        return self._config.get(key, default)
