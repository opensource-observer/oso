import json
import typing as t
from datetime import datetime, timezone
from io import StringIO

import structlog
from google.cloud import storage

logger = structlog.get_logger(__name__)


class BufferedBoundLogger:
    def __init__(
        self, base_logger: structlog.BoundLogger, buffer: "GCSLogBufferProcessor"
    ):
        self._logger = base_logger
        self._buffer = buffer

    def _proxy_method(self, method_name: str):
        def method(event: str | None = None, **kw: t.Any):
            event_dict = dict(kw)
            if event is not None:
                event_dict["event"] = event
            self._buffer(None, method_name, event_dict)
            return getattr(self._logger, method_name)(event, **kw)

        return method

    def bind(self, **new_values: t.Any) -> "BufferedBoundLogger":
        """Bind new values and return a new BufferedBoundLogger with the same buffer."""
        return BufferedBoundLogger(self._logger.bind(**new_values), self._buffer)

    @property
    def bindings(self) -> dict[str, t.Any]:
        """Return the bindings from the underlying logger."""
        return self._logger._context._dict  # type: ignore

    def __getattr__(self, name: str):
        if name in ("debug", "info", "warning", "error", "critical", "exception"):
            return self._proxy_method(name)
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
            logger.warning("No logs to flush for run", extra={"run_id": self.run_id})
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
            logger.info(
                "Successfully uploaded logs to GCS",
                extra={
                    "run_id": self.run_id,
                    "gcs_url": gcs_url,
                    "log_count": len(self.buffer),
                },
            )
            return gcs_url
        except Exception as e:
            logger.error(
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
