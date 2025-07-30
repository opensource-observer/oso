"""
Some potentially useful logging decorators
"""

import functools
import logging


def time_function(logger: logging.Logger):
    """Decorator to time a function and log the duration."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Function {func.__name__} took {duration:.4f} seconds")
            return result

        return wrapper

    return decorator
