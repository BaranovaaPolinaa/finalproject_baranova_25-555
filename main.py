import logging
from typing import Optional

from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.storage import load_rates
from valutatrade_hub.core.services import UserManager, PortfolioManager
from valutatrade_hub.core.exceptions import ApiRequestError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

user_manager = UserManager()
portfolio_manager = PortfolioManager(user_manager)
current_user: Optional[str] = None

coingecko_client = CoinGeckoClient()
exchangerate_client = ExchangeRateApiClient()


def update_rates(source: Optional[str] = None):
    """Обновление курсов валют через API"""
    clients = []
    if source is None or source.lower() == "coingecko":
        clients.append(coingecko_client)
    if source is None or source.lower() == "exchangerate":
        clients.append(exchangerate_client)

    updater = RatesUpdater(clients)
    try:
        total = updater.run_update()
        print(f"Обновление завершено. Всего пар: {total}")
    except ApiRequestError as exc:
        print(f"Ошибка обновления: {exc}")


def show_rates(currency: Optional[str] = None, top: Optional[int] = None, base: str = "USD"):
    """Показать локальные курсы валют"""
    data = load_rates()
    pairs = data.get("pairs", {})
    last_refresh = data.get("last_refresh", "N/A")

    if not pairs:
        print("Локальный кеш курсов пуст. Выполните 'update-rates'.")
        return

    filtered = {}
    base = base.upper()
    for key, info in pairs.items():
        from_cur, to_cur = key.split("_")
        if currency and from_cur.upper() != currency.upper():
            continue
        filtered[key] = info

    if top:
        filtered = dict(
            sorted(filtered.items(), key=lambda item: item[1]["rate"], reverse=True)[:top]
        )

    if currency and not filtered:
        print(f"Курс для '{currency}' не найден.")
        return

    print(f"Rates from cache (updated at {last_refresh}):")
    for key, info in filtered.items():
        print(f"- {key}: {info['rate']}")


def main():
    global current_user
    print("Добро пожаловать в ValutaTrade Hub! Введите 'help' для списка команд.")

    while True:
        cmd_input = input(">> ").strip()
        if not cmd_input:
            continue

        parts = cmd_input.split()
        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "help":
                print(
                    """
Команды:
register <username> <password>     — регистрация пользователя
login <username> <password>        — вход пользователя
buy <currency> <amount>            — купить валюту
sell <currency> <amount>           — продать валюту
show-portfolio                     — показать портфель пользователя с общей стоимостью
get-rate <currency>                — показать курс валюты
update-rates [source]              — обновить курсы (coingecko/exchangerate)
show-rates [currency] [top] [base] — показать локальные курсы
exit                               — выйти из CLI
"""
                )
            elif command == "register":
                if len(args) < 2:
                    print("Использование: register <username> <password>")
                    continue
                username, password = args
                user_manager.register(username, password)
                current_user = username
                print(f"Пользователь '{username}' успешно зарегистрирован и вошёл в систему.")
            elif command == "login":
                if len(args) < 2:
                    print("Использование: login <username> <password>")
                    continue
                username, password = args
                user_manager.login(username, password)
                current_user = username
                print(f"Пользователь '{username}' успешно вошёл в систему.")
            elif command == "buy":
                if not current_user:
                    print("Сначала выполните login.")
                    continue
                if len(args) < 2:
                    print("Использование: buy <currency> <amount>")
                    continue
                currency, amount = args
                portfolio_manager.buy(currency.upper(), float(amount))
                print(f"Куплено {amount} {currency.upper()}.")
            elif command == "sell":
                if not current_user:
                    print("Сначала выполните login.")
                    continue
                if len(args) < 2:
                    print("Использование: sell <currency> <amount>")
                    continue
                currency, amount = args
                portfolio_manager.sell(currency.upper(), float(amount))
                print(f"Продано {amount} {currency.upper()}.")
            elif command == "show-portfolio":
                if not current_user:
                    print("Сначала выполните login.")
                    continue
                portfolio = portfolio_manager.get_portfolio()
                total_value = portfolio.get_total_value()
                for wallet in portfolio.wallets.values():
                    print(f"{wallet.currency_code}: {wallet.balance}")
                print(f"Общая стоимость: {total_value} USD")
            elif command == "get-rate":
                if not args:
                    print("Использование: get-rate <currency>")
                    continue
                currency = args[0].upper()
                rate = portfolio_manager.get_rate(currency)
                print(f"Курс {currency}: {rate}")
            elif command == "update-rates":
                source = args[0] if args else None
                update_rates(source)
            elif command == "show-rates":
                currency = args[0] if len(args) >= 1 else None
                top = int(args[1]) if len(args) >= 2 else None
                base = args[2].upper() if len(args) >= 3 else "USD"
                show_rates(currency, top, base)
            elif command == "exit":
                print("Выход из CLI...")
                break
            else:
                print(f"Неизвестная команда '{command}'. Введите 'help' для списка команд.")
        except Exception as exc:
            print(f"Ошибка: {exc}")


if __name__ == "__main__":
    main()
