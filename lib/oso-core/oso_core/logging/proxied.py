import logging
import typing as t

from .types import BindableLogger


class ProxiedBoundLogger(BindableLogger):
    """Logger wrapper that proxies all calls to an underlying logger."""

    def __init__(
        self, proxied: list[BindableLogger], context: dict[str, t.Any] | None = None
    ):
        self._proxied_loggers = proxied
        self._inner_context = context or {}

    def bind(self, **new_values: t.Any) -> "ProxiedBoundLogger":
        return ProxiedBoundLogger(
            [logger.bind(**new_values) for logger in self._proxied_loggers],
            context={**self._inner_context, **new_values},
        )

    @property
    def _context(self) -> dict[str, t.Any]:
        # Return the context of the first proxied logger (they should all have the same context)
        return self._inner_context

    def debug(self, event: str, *args: t.Any, **kw: t.Any) -> None:
        self.log(logging.DEBUG, event, *args, **kw)

    def info(self, event: str, *args: t.Any, **kw: t.Any) -> None:
        self.log(logging.INFO, event, *args, **kw)

    def warning(self, event: str, *args: t.Any, **kw: t.Any) -> None:
        self.log(logging.WARNING, event, *args, **kw)

    def error(self, event: str, *args: t.Any, **kw: t.Any) -> None:
        self.log(logging.ERROR, event, *args, **kw)

    def critical(self, event: str, *args: t.Any, **kw: t.Any) -> None:
        self.log(logging.CRITICAL, event, *args, **kw)

    def exception(self, event: str, *args: t.Any, **kw: t.Any) -> None:
        self.log(logging.ERROR, event, *args, **kw)

    def log(self, level: int, event: str, *args: t.Any, **kw: t.Any) -> None:
        # Eagerly evaluate the event string and arguments to avoid issues with loggers that don't support lazy formatting
        new_event = event % args if args else event
        for logger in self._proxied_loggers:
            logger.log(level, new_event, **kw)
