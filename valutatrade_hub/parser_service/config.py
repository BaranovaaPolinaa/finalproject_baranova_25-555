import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParserConfig:
    EXCHANGERATE_API_KEY: str = os.getenv(
        "EXCHANGERATE_API_KEY",
        "ba2b2432e2f2464a15f1e647",
    )

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_FIAT_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")

    CRYPTO_ID_MAP: dict = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    })

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    REQUEST_TIMEOUT: int = 10
    UPDATE_INTERVAL_SECONDS: int = 300


config = ParserConfig()
