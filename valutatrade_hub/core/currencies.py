from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Currency name must be a non-empty string")

        if (
            not isinstance(code, str)
            or not code.isupper()
            or not 2 <= len(code) <= 5
            or " " in code
        ):
            raise ValueError(
                "Currency code must be 2–5 uppercase characters without spaces"
            )

        self.name: str = name
        self.code: str = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Return human-readable representation for UI/logs"""
        pass


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)

        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("Issuing country must be a non-empty string")

        self.issuing_country: str = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"
    

class CryptoCurrency(Currency):
    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float
    ):
        super().__init__(name, code)

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("Algorithm must be a non-empty string")

        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            raise ValueError("Market cap must be a non-negative number")

        self.algorithm: str = algorithm
        self.market_cap: float = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )
        

_CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
}


def get_currency(code: str) -> Currency:
    code = code.upper()

    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(f"Currency '{code}' not found")

    return _CURRENCY_REGISTRY[code]
