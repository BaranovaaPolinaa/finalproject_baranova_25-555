import logging
from datetime import datetime
from functools import wraps
from typing import Callable

from valutatrade_hub.core.usecases import _current_user

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    *,
    verbose: bool = False,
):
    """
    Декоратор логирования доменных операций.

    :param action: BUY / SELL / LOGIN / REGISTER
    :param verbose: логировать доп. контекст
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.now().isoformat()
            user = getattr(_current_user, "username", None)

            log_data = {
                "action": action,
                "user": user,
                "timestamp": timestamp,
            }

            try:
                result = func(*args, **kwargs)

                log_data["result"] = "OK"

                if verbose:
                    log_data["details"] = {
                        "args": args,
                        "kwargs": kwargs,
                    }

                logger.info(_format_log(log_data))
                return result

            except Exception as exc:
                log_data.update({
                    "result": "ERROR",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                })

                logger.info(_format_log(log_data))
                raise

        return wrapper

    return decorator


def _format_log(data: dict) -> str:
    """
    Приведение лог-записи к человекочитаемому виду
    """
    parts = [
        f"{data.get('action')}",
        f"user='{data.get('user')}'",
        f"result={data.get('result')}",
    ]

    if "error_type" in data:
        parts.append(f"error={data['error_type']}: {data['error_message']}")

    return " ".join(parts)
