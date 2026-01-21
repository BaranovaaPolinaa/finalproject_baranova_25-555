import logging
import threading
import time
from datetime import datetime

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import config
from .updater import RatesUpdater

logger = logging.getLogger(__name__)


class RateUpdaterScheduler:
    """
    Планировщик периодического обновления курсов.
    """

    def __init__(self, interval: int = config.UPDATE_INTERVAL_SECONDS):
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self.updater = RatesUpdater(
            clients=[
                ExchangeRateApiClient(),
                CoinGeckoClient(),
            ]
        )

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning("Scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        logger.info(f"RateUpdaterScheduler started (interval={self.interval}s)")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        logger.info("RateUpdaterScheduler stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                count = self.updater.run_update()
                logger.info(
                    f"[{datetime.now().isoformat()}Z] "
                    f"Updated {count} currency pairs"
                )
            except Exception as exc:
                logger.error(
                    f"[{datetime.now().isoformat()}Z] "
                    f"Update error: {exc}"
                )

            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)


scheduler = RateUpdaterScheduler()
