from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

from .config import config


class BaseApiClient(ABC):
    """
    Абстрактный базовый клиент для получения курсов валют.
    """

    @abstractmethod
    def fetch_rates(self) -> Dict[str, dict]:
        """
        Возвращает словарь вида:
        {
          "BTC_USD": {
              "rate": float,
              "timestamp": ISO,
              "source": str,
              "meta": dict
          },
          ...
        }
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """
    Клиент для получения курсов криптовалют через CoinGecko
    """

    def __init__(self):
        self.crypto_map = config.CRYPTO_ID_MAP
        self.base_currency = config.BASE_FIAT_CURRENCY.upper()

    def fetch_rates(self) -> Dict[str, dict]:
        ids = ",".join(self.crypto_map.values())
        url = (
            f"{config.COINGECKO_URL}"
            f"?ids={ids}&vs_currencies={self.base_currency.lower()}"
        )

        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(f"CoinGecko network error: {exc}")
        except ValueError:
            raise ApiRequestError("CoinGecko returned invalid JSON")

        timestamp = datetime.now().replace(tzinfo=timezone.utc).isoformat()
        result: Dict[str, dict] = {}

        for symbol, coin_id in self.crypto_map.items():
            if coin_id not in data:
                continue
            if self.base_currency.lower() not in data[coin_id]:
                continue

            rate = float(data[coin_id][self.base_currency.lower()])
            pair = f"{symbol}_{self.base_currency}"

            result[pair] = {
                "rate": rate,
                "timestamp": timestamp,
                "source": "CoinGecko",
                "meta": {
                    "raw_id": coin_id,
                    "status_code": response.status_code,
                },
            }

        return result


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент для получения фиатных курсов через ExchangeRate-API
    """

    def __init__(self):
        self.api_key = config.EXCHANGERATE_API_KEY
        self.base_currency = config.BASE_FIAT_CURRENCY.upper()

        if not self.api_key:
            raise ApiRequestError("ExchangeRate-API key not found in environment")

    def fetch_rates(self) -> Dict[str, dict]:
        url = (
            f"{config.EXCHANGERATE_API_URL}/"
            f"{self.api_key}/latest/{self.base_currency}"
        )

        try:
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError(f"ExchangeRate-API error: {data}")

        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(f"ExchangeRate-API network error: {exc}")
        except ValueError:
            raise ApiRequestError("ExchangeRate-API returned invalid JSON")

        timestamp = datetime.now().replace(tzinfo=timezone.utc).isoformat()
        result: Dict[str, dict] = {}

        for currency, rate in data.get("rates", {}).items():
            pair = f"{currency.upper()}_{self.base_currency}"

            result[pair] = {
                "rate": float(rate),
                "timestamp": timestamp,
                "source": "ExchangeRate-API",
                "meta": {
                    "status_code": response.status_code,
                },
            }

        return result
