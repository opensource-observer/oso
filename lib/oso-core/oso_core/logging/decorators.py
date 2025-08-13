"""
Some potentially useful logging decorators
"""

import functools
import logging


def time_function(logger: logging.Logger, override_name: str = ""):
    """Decorator to time a function and log the duration."""

    def decorator(func):
        name = override_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            duration_ms = duration * 1000
            logger.info(
                f"Function `{name}` took {duration_ms:.4f} milliseconds.",
                extra=dict(event_type="timing", duration_ms=duration_ms),
            )
            return result

        return wrapper

    return decorator
