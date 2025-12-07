import time
from typing import Callable, TypeVar

T = TypeVar("T")


class MaxRetriesExceeded(Exception):
    pass


def retry[T](
    command: Callable[[], T],
    error_handler: Callable[[Exception], None],
    initial_timeout: float = 0.5,
    max_retries: int = 10,
) -> T:
    timeout = initial_timeout
    for i in range(max_retries):
        try:
            return command()
        except Exception as exc:
            error_handler(exc)
        time.sleep(timeout)
        timeout += timeout

    raise MaxRetriesExceeded()
