"""
A simple heartbeat resource to indicate liveness of Dagster jobs.
"""

import asyncio
import concurrent.futures
import logging
import typing as t
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from queue import Empty, Queue

import aiofiles
import dagster as dg
from pydantic import Field
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

BeatLoopFunc = t.Callable[..., t.Coroutine[None, None, None]]


def run_beat_loop(
    interval_seconds: int,
    queue: Queue[bool],
    beat_loop_func: BeatLoopFunc,
    beat_loop_kwargs: dict[str, t.Any],
) -> None:
    logger.info("Starting heartbeat beat loop")
    while True:
        logger.info("Running heartbeat beat loop function")
        asyncio.run(beat_loop_func(**beat_loop_kwargs))
        try:
            if queue.get(timeout=interval_seconds):
                logger.info("Stopping heartbeat beat loop")
                break
        except Empty:
            continue


class HeartBeatResource(dg.ConfigurableResource):
    def beat_loop_func(self) -> BeatLoopFunc:
        raise NotImplementedError()

    def beat_loop_kwargs(self) -> dict[str, t.Any]:
        return {}

    async def get_last_heartbeat_for(self, name: str) -> datetime | None:
        raise NotImplementedError()

    async def beat(self, heartbeat_name: str) -> None:
        raise NotImplementedError()

    @asynccontextmanager
    async def heartbeat(
        self,
        name: str,
        interval_seconds: int = 120,
        log_override: logging.Logger | None = None,
    ) -> t.AsyncIterator[None]:
        log_override = log_override or logger
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            kwargs = self.beat_loop_kwargs().copy()
            kwargs.update({"heartbeat_name": name})
            queue = Queue[bool]()
            beat_task = loop.run_in_executor(
                executor,
                run_beat_loop,
                interval_seconds,
                queue,
                self.beat_loop_func(),
                kwargs,
            )
            try:
                yield
            finally:
                queue.put(True)
                beat_task.cancel()
                with suppress(asyncio.CancelledError):
                    await beat_task


@asynccontextmanager
async def async_redis_client(host: str, port: int) -> t.AsyncIterator[Redis]:
    client = Redis(host=host, port=port)
    try:
        yield client
    finally:
        await client.aclose()


async def redis_send_heartbeat(*, host: str, port: int, heartbeat_name: str) -> None:
    async with async_redis_client(host, port) as redis_client:
        await redis_client.set(
            f"heartbeat:{heartbeat_name}", datetime.now(timezone.utc).isoformat()
        )


class RedisHeartBeatResource(HeartBeatResource):
    host: str = Field(description="Redis host for heartbeat storage.")
    port: int = Field(default=6379, description="Redis port for heartbeat storage.")

    def beat_loop_func(self) -> BeatLoopFunc:
        return redis_send_heartbeat

    def beat_loop_kwargs(self) -> dict[str, t.Any]:
        return {"host": self.host, "port": self.port}

    async def get_last_heartbeat_for(self, name: str) -> datetime | None:
        async with async_redis_client(self.host, self.port) as redis_client:
            timestamp = await redis_client.get(f"heartbeat:{name}")
            logger.info(f"Fetched heartbeat `{name}`: {timestamp}")
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, bytes):
                return datetime.fromisoformat(timestamp.decode("utf-8"))
            else:
                return None

    async def beat(self, heartbeat_name: str) -> None:
        return await redis_send_heartbeat(
            host=self.host, port=self.port, heartbeat_name=heartbeat_name
        )


async def filebased_send_heartbeat(*, directory: str, heartbeat_name: str) -> None:
    from pathlib import Path

    import aiofiles

    filepath = Path(directory) / f"{heartbeat_name}_heartbeat.txt"
    async with aiofiles.open(filepath, mode="w") as f:
        await f.write(datetime.now(timezone.utc).isoformat())


class FilebasedHeartBeatResource(HeartBeatResource):
    """A simple file-based heartbeat resource. Intended for local development and testing."""

    directory: str = Field(description="Directory to store heartbeat files.")

    async def get_last_heartbeat_for(self, name: str) -> datetime | None:
        from pathlib import Path

        filepath = Path(self.directory) / f"{name}_heartbeat.txt"
        if not filepath.exists():
            return None
        async with aiofiles.open(filepath, mode="r") as f:
            timestamp = await f.read()
            return datetime.fromisoformat(timestamp)

    async def beat(self, heartbeat_name: str) -> None:
        from pathlib import Path

        import aiofiles

        filepath = Path(self.directory) / f"{heartbeat_name}_heartbeat.txt"
        async with aiofiles.open(filepath, mode="w") as f:
            await f.write(datetime.now(timezone.utc).isoformat())

    @asynccontextmanager
    async def heartbeat(
        self,
        name: str,
        interval_seconds: int = 120,
        log_override: logging.Logger | None = None,
    ) -> t.AsyncIterator[None]:
        logger_to_use = log_override or logger

        async def beat_loop():
            while True:
                try:
                    await self.beat(name)
                    logger_to_use.info(
                        f"Heartbeat sent for job {name} at {datetime.now(timezone.utc).isoformat()}"
                    )
                except Exception as e:
                    logger_to_use.error(f"Error sending heartbeat for job {name}: {e}")
                await asyncio.sleep(interval_seconds)

        beat_task = asyncio.create_task(beat_loop())
        try:
            yield
        finally:
            beat_task.cancel()
            with suppress(asyncio.CancelledError):
                await beat_task
