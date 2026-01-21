from datetime import datetime
from typing import Optional

from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
    ValidationError,
)
from valutatrade_hub.core.utils import (
    validate_amount,
    validate_currency_code,
)


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency_code = validate_currency_code(currency_code)
        self._balance = 0.0
        self.balance = balance

    @property
    def currency_code(self) -> str:
        return self._currency_code

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Баланс должен быть неотрицательным числом")
        self._balance = float(value)

    def deposit(self, amount: float):
        validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float):
        validate_amount(amount)

        if amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: "
                "доступно {self._balance} {self._currency_code}, "
                f"требуется {amount} {self._currency_code}"
            )

        self._balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency_code": self._currency_code,
            "balance": self._balance,
        }


class Portfolio:
    def __init__(self, user_id: int, wallets: Optional[dict[str, Wallet]] = None):
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = wallets if wallets is not None else {}

    @property
    def user(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        currency_code = validate_currency_code(currency_code)

        if currency_code in self._wallets:
            return

        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Wallet:
        currency_code = validate_currency_code(currency_code)

        if currency_code not in self._wallets:
            raise CurrencyNotFoundError(f"Неизвестная валюта '{currency_code}'")

        return self._wallets[currency_code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        base_currency = validate_currency_code(base_currency)

        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 50000.0,
            "ETH": 3000.0,
        }

        if base_currency not in exchange_rates:
            raise ValidationError(
                f"Нет доступного курса для базовой валюты '{base_currency}'"
            )

        total_usd = 0.0

        for wallet in self._wallets.values():
            if wallet.currency_code not in exchange_rates:
                continue

            total_usd += wallet.balance * exchange_rates[wallet.currency_code]

        return total_usd / exchange_rates[base_currency]
