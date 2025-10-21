"""
A simple heartbeat resource to indicate liveness of Dagster jobs.
"""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone

import aiofiles
import dagster as dg
from pydantic import Field
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class HeartBeatResource(dg.ConfigurableResource):
    async def get_last_heartbeat_for(self, job_name: str) -> datetime | None:
        raise NotImplementedError()

    async def beat(self, job_name: str) -> None:
        raise NotImplementedError()

    @asynccontextmanager
    async def heartbeat(
        self,
        job_name: str,
        interval_seconds: int = 120,
        log_override: logging.Logger | None = None,
    ):
        """
        asynchronously run a heartbeat that updates every `interval_seconds`
        """

        log_override = log_override or logger

        async def _beat_loop():
            log_override.info(
                f"Starting heartbeat for job {job_name} every {interval_seconds} seconds"
            )
            while True:
                log_override.info(f"Beating heartbeat for job {job_name}")
                await self.beat(job_name)
                await asyncio.sleep(interval_seconds)

        task = asyncio.create_task(_beat_loop())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


class RedisHeartBeatResource(HeartBeatResource):
    host: str = Field(description="Redis host for heartbeat storage.")
    port: int = Field(default=6379, description="Redis port for heartbeat storage.")

    async def get_last_heartbeat_for(self, job_name: str) -> datetime | None:
        redis_client = Redis(host=self.host, port=self.port, decode_responses=True)
        timestamp = await redis_client.get(f"heartbeat:{job_name}")
        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)
        else:
            return None

    async def beat(self, job_name: str) -> None:
        redis_client = Redis(host=self.host, port=self.port, decode_responses=True)
        await redis_client.set(
            f"heartbeat:{job_name}", datetime.now(timezone.utc).isoformat()
        )


class FilebasedHeartBeatResource(HeartBeatResource):
    """A simple file-based heartbeat resource. Intended for local development and testing."""

    directory: str = Field(description="Directory to store heartbeat files.")

    async def get_last_heartbeat_for(self, job_name: str) -> datetime | None:
        from pathlib import Path

        filepath = Path(self.directory) / f"{job_name}_heartbeat.txt"
        if not filepath.exists():
            return None
        async with aiofiles.open(filepath, mode="r") as f:
            timestamp = await f.read()
            return datetime.fromisoformat(timestamp)

    async def beat(self, job_name: str) -> None:
        from pathlib import Path

        import aiofiles

        filepath = Path(self.directory) / f"{job_name}_heartbeat.txt"
        async with aiofiles.open(filepath, mode="w") as f:
            await f.write(datetime.now(timezone.utc).isoformat())
