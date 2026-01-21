import json
from pathlib import Path

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"

DATA_DIR.mkdir(exist_ok=True)

def load_users():
    if USERS_FILE.exists():
        return json.load(open(USERS_FILE, encoding="utf-8"))
    return []

def save_users(users):
    DATA_DIR.mkdir(exist_ok=True)
    json.dump(users, open(USERS_FILE, "w", encoding="utf-8"), indent=2)

def load_portfolios():
    if PORTFOLIOS_FILE.exists():
        return json.load(open(PORTFOLIOS_FILE, encoding="utf-8"))
    return {}

def save_portfolios(portfolios):
    DATA_DIR.mkdir(exist_ok=True)
    json.dump(portfolios, open(PORTFOLIOS_FILE, "w", encoding="utf-8"), indent=2)

current_user = None

users = load_users()
portfolios = load_portfolios()


def register_user(username: str, password: str):
    if any(user["username"] == username for user in users):
        return False, "Пользователь существует"
    users.append({"username": username, "password": password})
    save_users(users)
    global current_user
    current_user = username
    return True, f"Пользователь {username} зарегистрирован"


def login_user(username: str, password: str):
    global current_user
    for user in users:
        if user["username"] == username and user["password"] == password:
            current_user = username
            return True, f"Пользователь {username} вошёл в систему"
    return False, "Неверное имя пользователя или пароль"


def buy_currency(currency: str, amount: float):
    if not current_user:
        return False, "Сначала выполните login"
    user_portfolio = portfolios.get(current_user, {})
    user_portfolio[currency] = user_portfolio.get(currency, 0) + amount
    portfolios[current_user] = user_portfolio
    save_portfolios(portfolios)
    return True, f"Куплено {amount} {currency}"


def sell_currency(currency: str, amount: float):
    if not current_user:
        return False, "Сначала выполните login"
    user_portfolio = portfolios.get(current_user, {})
    if user_portfolio.get(currency, 0) < amount:
        return False, f"Недостаточно {currency} для продажи"
    user_portfolio[currency] -= amount
    portfolios[current_user] = user_portfolio
    save_portfolios(portfolios)
    return True, f"Продано {amount} {currency}"


def show_portfolio():
    if not current_user:
        return False, "Сначала выполните login"
    return True, portfolios.get(current_user, {})
