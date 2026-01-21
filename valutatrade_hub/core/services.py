import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from valutatrade_hub.core.models import Portfolio, User, Wallet

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"

DATA_DIR.mkdir(exist_ok=True)

if not USERS_FILE.exists():
    USERS_FILE.write_text("[]", encoding="utf-8")

if not PORTFOLIOS_FILE.exists():
    PORTFOLIOS_FILE.write_text("[]", encoding="utf-8")

class UserManager:
    def __init__(self):
        self._current_user: User | None = None
        self._load_users()

    def _load_users(self):
        self._users = json.loads(USERS_FILE.read_text(encoding="utf-8"))

    def _save_users(self):
        USERS_FILE.write_text(json.dumps(self._users, indent=2), encoding="utf-8")

    def register(self, username: str, password: str):
        if any(user["username"] == username for user in self._users):
            raise ValueError(f"Пользователь '{username}' уже существует")
        hashed = sha256(password.encode()).hexdigest()
        user = {
            "user_id": len(self._users) + 1,
            "username": username,
            "password": hashed,
            "created_at": datetime.now().isoformat()
        }
        self._users.append(user)
        self._save_users()
        self._current_user = User(
            user["user_id"], 
            user["username"], 
            hashed, "", 
            datetime.now()
        )
        return self._current_user

    def login(self, username: str, password: str):
        hashed = sha256(password.encode()).hexdigest()
        data = next((
            user for user in self._users 
            if user["username"] == username and user["password"] == hashed), None
        )
        if not data:
            raise ValueError("Неверный логин или пароль")
        self._current_user = User(
            data["user_id"], 
            data["username"], hashed, "", datetime.now()
        )
        return self._current_user

    @property
    def current_user(self):
        return self._current_user

class PortfolioManager:
    def __init__(self, user_manager: UserManager):
        self._user_manager = user_manager
        self._load_portfolios()

    def _load_portfolios(self):
        self._portfolios_data = json.loads(PORTFOLIOS_FILE.read_text(encoding="utf-8"))
        self._portfolios = {}
        for portfolio in self._portfolios_data:
            user_id = portfolio["user_id"]
            wallets = {
                currency: Wallet(currency, balance)
                for currency, balance in portfolio.get("wallets", {}).items()
            }
            self._portfolios[user_id] = Portfolio(user_id, wallets)

    def _save_portfolios(self):
        data = []
        for portfolio in self._portfolios.values():
            wallets = {
                wallet.currency_code: wallet.balance
                for wallet in portfolio.wallets.values()
            }
            data.append({"user_id": portfolio.user, "wallets": wallets})
        PORTFOLIOS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_portfolio(self):
        user = self._user_manager.current_user
        if not user:
            raise ValueError("Сначала выполните login")
        if user.user_id not in self._portfolios:
            self._portfolios[user.user_id] = Portfolio(user.user_id)
        return self._portfolios[user.user_id]

    def buy(self, currency_code: str, amount: float):
        portfolio = self.get_portfolio()
        portfolio.add_currency(currency_code)
        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        self._save_portfolios()
        return wallet

    def sell(self, currency_code: str, amount: float):
        portfolio = self.get_portfolio()
        wallet = portfolio.get_wallet(currency_code)
        wallet.withdraw(amount)
        self._save_portfolios()
        return wallet
    
    def get_rate(self, currency_code: str) -> float:
        """
        Возвращает текущий курс валюты относительно USD.
        Для простоты можно брать из жестко закодированного словаря
        или потом интегрировать с parser_service.
        """
        currency_code = currency_code.upper()
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 20.0,
        }

        if currency_code not in exchange_rates:
            raise ValueError(f"Нет доступного курса для валюты '{currency_code}'")

        return exchange_rates[currency_code]
