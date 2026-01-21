import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthRequiredError,
    InsufficientFundsError,
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import validate_amount, validate_currency_code
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader

settings = SettingsLoader()

DATA_DIR = settings.get("DATA_DIR", "data")
USERS_FILE = os.path.join(DATA_DIR, settings.get("USERS_FILE", "users.json"))
PORTFOLIOS_FILE = os.path.join(
    DATA_DIR, settings.get("PORTFOLIOS_FILE", "portfolios.json")
)
RATES_FILE = os.path.join(DATA_DIR, settings.get("RATES_FILE", "rates.json"))
RATES_TTL = settings.get("RATES_TTL_SECONDS", 300)

_current_user: Optional[User] = None


def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()


def _require_login():
    if _current_user is None:
        raise AuthRequiredError("Сначала выполните login")


def _get_rate(from_code: str, to_code: str) -> dict:
    """
    Получение курса с учётом TTL.
    Любая проблема → ApiRequestError (строго по ТЗ)
    """
    try:
        rates = _load_json(RATES_FILE, {})
        key = f"{from_code.upper()}_{to_code.upper()}"

        if key not in rates.get("pairs", {}):
            raise ApiRequestError(f"Курс {from_code}->{to_code} недоступен")

        updated_at = datetime.fromisoformat(rates["pairs"][key]["updated_at"])
        if datetime.now() - updated_at > timedelta(seconds=RATES_TTL):
            raise ApiRequestError(f"Курс {from_code}->{to_code} устарел")

        return rates["pairs"][key]

    except (OSError, ValueError, KeyError) as exc:
        raise ApiRequestError(f"Ошибка при обращении к внешнему API: {exc}")


@log_action("REGISTER")
def register_user(username: str, password: str) -> str:
    if not username or not username.strip():
        raise ValidationError("Имя пользователя не может быть пустым")
    if len(password) < 4:
        raise ValidationError("Пароль должен быть не короче 4 символов")

    users = _load_json(USERS_FILE, [])
    if any(user["username"] == username for user in users):
        raise UserAlreadyExistsError(f"Имя пользователя '{username}' уже занято")

    user_id = max((user["user_id"] for user in users), default=0) + 1
    salt = secrets.token_hex(8)
    hashed = _hash_password(password, salt)

    users.append({
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": datetime.now().isoformat(),
    })
    _save_json(USERS_FILE, users)

    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolios.append({"user_id": user_id, "wallets": {}})
    _save_json(PORTFOLIOS_FILE, portfolios)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})"


@log_action("LOGIN")
def login_user(username: str, password: str) -> str:
    global _current_user

    users = _load_json(USERS_FILE, [])
    data = next((user for user in users if user["username"] == username), None)
    if not data:
        raise UserNotFoundError(f"Пользователь '{username}' не найден")
    if _hash_password(password, data["salt"]) != data["hashed_password"]:
        raise InvalidPasswordError("Неверный пароль")

    _current_user = User(
        user_id=data["user_id"],
        username=data["username"],
        hashed_password=data["hashed_password"],
        salt=data["salt"],
        registration_date=datetime.fromisoformat(data["registration_date"]),
    )

    return f"Вы вошли как '{username}'"


def _load_portfolio() -> tuple[list, dict]:
    portfolios = _load_json(PORTFOLIOS_FILE, [])
    pdata = next(
        portfolio 
        for portfolio in portfolios if portfolio["user_id"] == _current_user.user_id
    )
    return portfolios, pdata


def _build_portfolio(pdata: dict) -> Portfolio:
    wallets = {
        code: Wallet(code, data["balance"])
        for code, data in pdata["wallets"].items()
    }
    return Portfolio(_current_user.user_id, wallets)


def _save_portfolio(portfolios: list, pdata: dict, portfolio: Portfolio):
    pdata["wallets"] = {
        code: {"balance": wallet.balance}
        for code, wallet in portfolio.wallets.items()
    }
    _save_json(PORTFOLIOS_FILE, portfolios)


def show_portfolio(base_currency: str = "USD") -> str:
    _require_login()

    base_currency = validate_currency_code(base_currency)
    get_currency(base_currency)

    portfolios, pdata = _load_portfolio()
    portfolio = _build_portfolio(pdata)

    if not portfolio.wallets:
        return "Портфель пуст"

    total = 0.0
    lines = [
        f"Портфель пользователя '{_current_user.username}' (база: {base_currency}):"
    ]

    for wallet in portfolio.wallets.values():
        code = wallet.currency_code
        get_currency(code)

        value = (
            wallet.balance 
            if code == base_currency 
            else wallet.balance * _get_rate(code, base_currency)["rate"]
        )
        total += value
        lines.append(f"- {code}: {wallet.balance:.4f} → {value:.2f} {base_currency}")

    lines.append("-" * 30)
    lines.append(f"ИТОГО: {total:,.2f} {base_currency}")
    return "\n".join(lines)


@log_action("BUY", verbose=True)
def buy_currency(currency_code: str, amount: float) -> str:
    _require_login()

    currency_code = validate_currency_code(currency_code)
    validate_amount(amount)
    get_currency(currency_code)

    portfolios, pdata = _load_portfolio()
    portfolio = _build_portfolio(pdata)

    rate = _get_rate(currency_code, "USD")["rate"]
    cost_usd = amount * rate

    portfolio.add_currency("USD")
    usd_wallet = portfolio.get_wallet("USD")

    if usd_wallet.balance < cost_usd:
        raise InsufficientFundsError(
            f"Недостаточно средств: доступно {usd_wallet.balance:.2f} USD, "
            f"требуется {cost_usd:.2f} USD"
        )

    usd_wallet.withdraw(cost_usd)
    portfolio.add_currency(currency_code)
    portfolio.get_wallet(currency_code).deposit(amount)

    _save_portfolio(portfolios, pdata, portfolio)

    return (
        f"Куплено {amount:.4f} {currency_code} "
        f"по курсу {rate:.2f} USD/{currency_code} "
        f"(стоимость {cost_usd:.2f} USD)"
    )


@log_action("SELL", verbose=True)
def sell_currency(currency_code: str, amount: float) -> str:
    _require_login()

    currency_code = validate_currency_code(currency_code)
    validate_amount(amount)
    get_currency(currency_code)

    portfolios, pdata = _load_portfolio()
    portfolio = _build_portfolio(pdata)

    wallet = portfolio.get_wallet(currency_code)

    if amount > wallet.balance:
        raise InsufficientFundsError(
            f"Недостаточно средств: доступно {wallet.balance:.4f} {currency_code}, "
            f"требуется {amount:.4f} {currency_code}"
        )

    rate = _get_rate(currency_code, "USD")["rate"]
    revenue = amount * rate

    wallet.withdraw(amount)
    portfolio.add_currency("USD")
    portfolio.get_wallet("USD").deposit(revenue)

    _save_portfolio(portfolios, pdata, portfolio)

    return (
        f"Продано {amount:.4f} {currency_code} "
        f"по курсу {rate:.2f} USD/{currency_code} "
        f"(выручка {revenue:.2f} USD)"
    )


def get_rate(from_code: str, to_code: str) -> str:
    from_code = validate_currency_code(from_code)
    to_code = validate_currency_code(to_code)

    get_currency(from_code)
    get_currency(to_code)

    rate = _get_rate(from_code, to_code)
    return (
        f"Курс {from_code}→{to_code}: {rate['rate']} (обновлено: {rate['updated_at']})"
    )
