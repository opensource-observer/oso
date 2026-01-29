import json
import logging
import typing as t
from datetime import datetime, timezone
from io import StringIO
from typing import Protocol

from google.cloud import storage

system_logger = logging.getLogger(__name__)


class BindableLogger(Protocol):
    """Protocol for loggers that support structlog's bind() method."""

    def bind(self, **new_values: t.Any) -> "BindableLogger": ...

    @property
    def bindings(self) -> dict[str, t.Any]: ...

    def debug(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def info(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def warning(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def error(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def critical(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def exception(self, event: str | None = None, **kw: t.Any) -> t.Any: ...


class BufferedBoundLogger(BindableLogger):
    """Logger wrapper that buffers log entries and delegates to an underlying logger."""

    _LOG_METHODS = ("debug", "info", "warning", "error", "critical", "exception")

    def __init__(self, base_logger: BindableLogger, buffer: "GCSLogBufferProcessor"):
        self._logger = base_logger
        self._buffer = buffer

        for method_name in self._LOG_METHODS:
            setattr(self, method_name, self._create_proxy_method(method_name))

    def _create_proxy_method(self, method_name: str):
        """Create a proxy method that logs to buffer and delegates to underlying logger."""

        def method(event: str | None = None, **kw: t.Any):
            event_dict = dict(kw)
            if event is not None:
                event_dict["event"] = event
            self._buffer(None, method_name, event_dict)
            try:
                getattr(system_logger, method_name)(event, **kw)
            except Exception:
                system_logger.fatal("Failed to log to system logger", exc_info=True)
            try:
                getattr(self._logger, method_name)(event, **kw)
            except Exception:
                system_logger.fatal("Failed to log to underlying logger", exc_info=True)
            return getattr(self._logger, method_name)(event, **kw)

        return method

    def bind(self, **new_values: t.Any) -> "BufferedBoundLogger":
        """Bind new values and return a new BufferedBoundLogger with the same buffer."""
        return BufferedBoundLogger(self._logger.bind(**new_values), self._buffer)

    @property
    def bindings(self) -> dict[str, t.Any]:
        """Return the bindings from the underlying logger."""
        return self._logger.bindings

    def debug(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def info(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def warning(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def error(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def critical(self, event: str | None = None, **kw: t.Any) -> t.Any: ...
    def exception(self, event: str | None = None, **kw: t.Any) -> t.Any: ...

    def __getattr__(self, name: str):
        return getattr(self._logger, name)


class GCSLogBufferProcessor:
    def __init__(self, run_id: str, gcs_bucket: str, gcs_project: str):
        self.run_id = run_id
        self.gcs_bucket = gcs_bucket
        self.gcs_project = gcs_project
        self.buffer: list[dict] = []
        self._storage_client: storage.Client | None = None

    def __call__(
        self,
        _logger: t.Any,
        method_name: str,
        event_dict: dict[str, t.Any],
    ) -> None:
        buffered_event = dict(event_dict)
        buffered_event["log_level"] = method_name
        buffered_event["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.buffer.append(buffered_event)

    async def flush(self, status: str = "unknown") -> str:
        if not self.buffer:
            system_logger.warning(
                "No logs to flush for run", extra={"run_id": self.run_id}
            )
            return ""

        if self._storage_client is None:
            self._storage_client = storage.Client(project=self.gcs_project)

        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        blob_name = f"run-logs/{date_prefix}/{self.run_id}/{status}.jsonl"

        log_content = StringIO()
        for log_entry in self.buffer:
            log_content.write(json.dumps(log_entry) + "\n")

        try:
            bucket = self._storage_client.bucket(self.gcs_bucket)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(
                log_content.getvalue(), content_type="application/jsonl"
            )

            gcs_url = f"gs://{self.gcs_bucket}/{blob_name}"
            system_logger.info(
                "Successfully uploaded logs to GCS",
                extra={
                    "run_id": self.run_id,
                    "gcs_url": gcs_url,
                    "log_count": len(self.buffer),
                },
            )
            return gcs_url
        except Exception as e:
            system_logger.error(
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
