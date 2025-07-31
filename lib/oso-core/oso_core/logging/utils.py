import logging
from contextlib import contextmanager


@contextmanager
def time_context(logger: logging.Logger, name: str, **log_kwargs):
    """Context manager to measure the timing of a block of code and log the
    duration."""
    import time

    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        duration_ms = duration * 1000
        logger.info(
            f"Timing `{name}` took {duration_ms:.4f} milliseconds.",
            extra=dict(
                event_type="timing",
                duration_ms=duration_ms,
                **log_kwargs,
            ),
        )
