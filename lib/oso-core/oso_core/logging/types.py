import abc
import typing as t
from dataclasses import dataclass
from datetime import datetime


class BindableLogger(t.Protocol):
    """Protocol for loggers that support structlog's bind() method."""

    @property
    def _context(self) -> dict[str, t.Any]: ...

    def bind(self, **new_values: t.Any) -> "BindableLogger": ...

    def debug(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def info(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def warning(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def error(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def critical(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def exception(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...

    def log(self, level: int, event: str, *args: t.Any, **kw: t.Any) -> None: ...


@dataclass
class LogEntry:
    timestamp: datetime
    log_level: str
    event: str
    args: tuple
    extra: dict[str, t.Any]

    def to_dict(self) -> dict[str, t.Any]:
        formatted_event = self.event
        if self.args:
            formatted_event = self.event % self.args
        return {
            "timestamp": self.timestamp.isoformat(),
            "log_level": self.log_level,
            "event": formatted_event,
            **self.extra,
        }


class LogBuffer(abc.ABC):
    @abc.abstractmethod
    def add(self, entry: LogEntry) -> None:
        """Add a log entry to the buffer."""
        raise NotImplementedError("add must be implemented by subclasses.")

    @abc.abstractmethod
    async def flush(self) -> None:
        """Flush the buffer to the underlying storage."""
        raise NotImplementedError("flush must be implemented by subclasses.")
