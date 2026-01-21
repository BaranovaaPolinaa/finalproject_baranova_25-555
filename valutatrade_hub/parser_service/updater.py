import logging
from datetime import datetime, timezone
from typing import List

from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.config import config

from .api_clients import BaseApiClient
from .storage import save_atomic

settings = SettingsLoader()
DATA_DIR = settings.get("DATA_DIR", "data")
RATES_FILE = config.RATES_FILE_PATH

logger = logging.getLogger(__name__)

class RatesUpdater:
    """
    Координация обновления всех валютных курсов.
    """
    def __init__(self, clients: List[BaseApiClient]):
        self.clients = clients

    def run_update(self):
        """
        1. Получаем данные от всех клиентов
        2. Объединяем словари
        3. Добавляем метаданные last_refresh
        4. Сохраняем в rates.json
        5. Логируем шаги
        """
        all_rates = {}
        for client in self.clients:
            try:
                client_rates = client.fetch_rates()
                all_rates.update(client_rates)
                logger.info(
                    f"{client.__class__.__name__}"
                    "успешно обновил {len(client_rates)} пар"
                )
            except Exception as exc:
                logger.error(
                    f"{client.__class__.__name__} не удалось получить данные: {exc}"
                )

        timestamp = datetime.now().replace(tzinfo=timezone.utc).isoformat()
        final_data = {
            "pairs": all_rates,
            "last_refresh": timestamp
        }

        save_atomic(final_data, RATES_FILE)
        logger.info(f"Обновление завершено. Всего пар: {len(all_rates)}")
        return len(all_rates)


if __name__ == "__main__":
    from .api_clients import CoinGeckoClient, ExchangeRateApiClient

    logging.basicConfig(level=logging.INFO)

    clients = [ExchangeRateApiClient(), CoinGeckoClient()]
    updater = RatesUpdater(clients)
    updater.run_update()
