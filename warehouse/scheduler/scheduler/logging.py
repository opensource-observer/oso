import abc
import json
import logging
import typing as t
from datetime import datetime, timezone
from io import StringIO
from typing import Protocol

import gcsfs
from attr import dataclass

module_system_logger = logging.getLogger(__name__)


class BindableLogger(Protocol):
    """Protocol for loggers that support structlog's bind() method."""

    def bind(self, **new_values: t.Any) -> "BindableLogger": ...

    def debug(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def info(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def warning(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def error(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def critical(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...
    def exception(self, event: str, *args: t.Any, **kw: t.Any) -> None: ...

    def log(self, level: int, event: str, *args: t.Any, **kw: t.Any) -> None: ...


class ProxiedBoundLogger(BindableLogger):
    """Logger wrapper that proxies all calls to an underlying logger."""

    def __init__(self, proxied: list[BindableLogger]):
        self._proxied_loggers = proxied

    def bind(self, **new_values: t.Any) -> "ProxiedBoundLogger":
        return ProxiedBoundLogger(
            [logger.bind(**new_values) for logger in self._proxied_loggers]
        )

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


@dataclass
class LogEntry:
    timestamp: datetime
    log_level: str
    event: str
    args: tuple
    extra: dict[str, t.Any]

    def to_dict(self) -> dict[str, t.Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "log_level": self.log_level,
            "event": self.event,
            "args": self.args,
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
            log_level=logging.getLevelName(level).lower(),
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


class GCSLogBuffer(LogBuffer):
    def __init__(
        self, run_id: str, gcs_client: gcsfs.GCSFileSystem, destination_path: str
    ):
        self.run_id = run_id
        self.gcs_client = gcs_client
        self.destination_path = destination_path
        self.buffer: list[LogEntry] = []

    def add(self, entry: LogEntry) -> None:
        self.buffer.append(entry)

    async def flush(self) -> None:
        if not self.buffer:
            module_system_logger.warning(
                "No logs to flush for run", extra={"run_id": self.run_id}
            )
            return None

        log_content = StringIO()
        for log_entry in self.buffer:
            log_content.write(json.dumps(log_entry.to_dict()) + "\n")

        try:
            await self.gcs_client._pipe_file(
                self.destination_path, log_content.getvalue().encode("utf-8")
            )

            gcs_url = f"gs://{self.destination_path}"
            module_system_logger.info(
                "Successfully uploaded logs to GCS",
                extra={
                    "run_id": self.run_id,
                    "gcs_url": gcs_url,
                    "log_count": len(self.buffer),
                },
            )
            return None
        except Exception as e:
            module_system_logger.error(
                "Failed to upload logs to GCS",
                extra={
                    "run_id": self.run_id,
                    "error": str(e),
                    "log_count": len(self.buffer),
                },
                exc_info=True,
            )
            raise

    def clear(self):
        self.buffer.clear()

    def get_log_count(self) -> int:
        return len(self.buffer)

    @property
    def destination_url(self) -> str:
        return f"gs://{self.destination_path}"
