import json
import logging
from datetime import datetime, timezone
from io import StringIO

import gcsfs
from oso_core.logging.buffered import BufferedLogger
from oso_core.logging.types import BindableLogger, LogEntry
from oso_dagster.resources.gcs import GCSFileResource
from scheduler.types import DestinationLogBuffer, RunLoggerContainer, RunLoggerFactory

module_system_logger = logging.getLogger(__name__)


class GCSRunLoggerFactory(RunLoggerFactory):
    def __init__(self, gcs: GCSFileResource, bucket: str):
        self._gcs = gcs
        self._bucket = bucket

    def create_logger_container(self, run_id: str) -> RunLoggerContainer:
        gcs_client = self._gcs.get_client(asynchronous=True)
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        log_destination_path = (
            f"{self._bucket}/run-logs/{date_prefix}/{run_id}/logs.jsonl"
        )
        return BufferedRunLoggerContainer.create_for_gcs(
            run_id=run_id,
            gcs_client=gcs_client,
            destination_path=log_destination_path,
        )


class BufferedRunLoggerContainer(RunLoggerContainer):
    @classmethod
    def create_for_gcs(
        cls,
        run_id: str,
        gcs_client: gcsfs.GCSFileSystem,
        destination_path: str,
    ) -> "BufferedRunLoggerContainer":
        log_buffer = GCSLogBuffer(run_id, gcs_client, destination_path)
        logger = BufferedLogger(log_buffer, context={"run_id": run_id})
        return cls(
            run_id=run_id,
            logger=logger,
            log_buffer=log_buffer,
        )

    def __init__(
        self,
        run_id: str,
        logger: BindableLogger,
        log_buffer: DestinationLogBuffer,
    ):
        self._run_id = run_id
        self._log_buffer = log_buffer
        self._logger = logger

    @property
    def logger(self) -> BindableLogger:
        return self._logger

    async def destination_uris(self) -> list[str]:
        # Flush logs to ensure all logs are uploaded before retrieving the
        # destination URI
        await self._log_buffer.flush()

        return await self._log_buffer.destination_uris()


class GCSLogBuffer(DestinationLogBuffer):
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

    async def destination_uris(self) -> list[str]:
        return [f"gs://{self.destination_path}"]
