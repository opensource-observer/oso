import logging
import typing as t
from datetime import datetime, timezone

from oso_core.logging.types import BindableLogger, LogBuffer, LogEntry


class BufferedLogger(BindableLogger):
    def __init__(self, buffer: LogBuffer, context: dict[str, t.Any] | None = None):
        self._buffer = buffer
        self._context = context or {}

    def bind(self, **new_values: t.Any) -> "BufferedLogger":
        new_context = self._context.copy()
        new_context.update(new_values)
        return BufferedLogger(self._buffer, new_context)

    def log(self, level: int, event: str, *args: t.Any, **kw: t.Any) -> None:
        log_entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            log_level=logging.getLevelName(level),
            event=event,
            args=args,
            extra={**self._context, **kw},
        )
        self._buffer.add(log_entry)

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
