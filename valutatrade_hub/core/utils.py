from valutatrade_hub.core.exceptions import ValidationError


def validate_currency_code(code: str) -> str:
    if not isinstance(code, str) or not code.strip():
        raise ValidationError("Currency code must be non-empty")

    code = code.upper()

    if not 2 <= len(code) <= 5 or " " in code:
        raise ValidationError("Invalid currency code format")

    return code


def validate_amount(amount: float):
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValidationError("'amount' must be a positive number")
    

def convert(amount: float, rate: float) -> float:
    return amount * rate
