class ValutaTradeError(Exception):
    """Базовое исключение проекта ValutaTrade Hub."""
    pass


class ApiRequestError(ValutaTradeError):
    """Ошибка при выполнении запроса к внешнему API."""
    pass


class AuthRequiredError(ValutaTradeError):
    """Ошибка авторизации."""
    pass


class UserAlreadyExistsError(ValutaTradeError):
    """
    Ошибка при регистрации пользователя,
    если пользователь с таким именем уже существует.
    """
    pass


class UserNotFoundError(ValutaTradeError):
    """Ошибка при попытке найти пользователя, которого не существует в системе."""
    pass


class InvalidPasswordError(ValutaTradeError):
    """Ошибка при проверке пароля, если введён неверный пароль пользователя."""
    pass


class CurrencyNotFoundError(ValutaTradeError):
    """
    Ошибка при работе с валютой, 
    которой нет в портфеле или в списке поддерживаемых валют.
    """
    pass


class InsufficientFundsError(ValutaTradeError):
    """Ошибка при попытке списания средств, если на кошельке недостаточно баланса."""
    pass


class ValidationError(ValutaTradeError):
    """Общее исключение для ошибок валидации данных."""
    pass