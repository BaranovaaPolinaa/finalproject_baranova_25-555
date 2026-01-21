import json
import os
import tempfile
from datetime import datetime, timezone

from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.config import config

settings = SettingsLoader()
DATA_DIR = settings.get("DATA_DIR") or "data"
RATES_FILE = config.RATES_FILE_PATH
EXCHANGE_RATES_FILE = config.HISTORY_FILE_PATH


def _ensure_dir(path: str):
    """Создаёт директорию, если её нет"""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _ensure_file(path: str, default_data):
    """Создаёт файл с дефолтными данными, если его нет"""
    if not path:
        raise ValueError("Путь к файлу пустой")
    _ensure_dir(path)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)


_ensure_file(RATES_FILE, {"pairs": {}, "last_refresh": None})
_ensure_file(EXCHANGE_RATES_FILE, {"records": []})


def load_rates(path: str = RATES_FILE) -> dict:
    """Загрузка курсов из файла"""
    if not path or not os.path.exists(path):
        return {"pairs": {}, "last_refresh": None}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"pairs": {}, "last_refresh": None}


def save_atomic(data: dict, path: str):
    """Сохраняет данные атомарно, чтобы не испортить файл при ошибке"""
    _ensure_dir(path)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
        json.dump(data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name
    os.replace(temp_name, path)


def update_rate_pair(
    from_currency: str,
    to_currency: str,
    rate: float,
    source: str,
    meta: dict | None = None,
):
    """Обновляет пару валют в основном и историческом файле"""
    rates = load_rates(RATES_FILE)
    pair_key = f"{from_currency.upper()}_{to_currency.upper()}"
    timestamp = datetime.now().replace(tzinfo=timezone.utc).isoformat()

    rates.setdefault("pairs", {})
    rates["pairs"][pair_key] = {
        "rate": rate,
        "updated_at": timestamp,
        "source": source,
        "meta": meta or {}
    }
    rates["last_refresh"] = timestamp
    save_atomic(rates, RATES_FILE)

    history = load_rates(EXCHANGE_RATES_FILE)
    history.setdefault("records", [])
    record = {
        "id": f"{pair_key}_{timestamp}",
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "rate": rate,
        "timestamp": timestamp,
        "source": source,
        "meta": meta or {}
    }
    history["records"].append(record)
    save_atomic(history, EXCHANGE_RATES_FILE)
    