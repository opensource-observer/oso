import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiofiles
import httpx
import structlog

logger = structlog.get_logger(__name__)

MAX_DOWNLOAD_ATTEMPTS = 3


async def stream_to_file(
    url: str, dest: str, read_timeout: int, chunk_size: int
) -> None:
    """Stream download to file with httpx."""
    logger.info("Streaming file to disk", url=url, dest=dest)
    httpx_timeout = httpx.Timeout(
        connect=30.0, read=float(read_timeout), write=30.0, pool=30.0
    )

    async with httpx.AsyncClient(
        timeout=httpx_timeout, follow_redirects=True
    ) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async with aiofiles.open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                    await f.write(chunk)

    logger.info("Stream to disk complete", url=url, dest=dest)


@asynccontextmanager
async def download_to_temp(
    url: str, suffix: str, read_timeout: int
) -> AsyncIterator[str]:
    """Stream download to temp disk with retry, auto-cleanup on exit."""
    chunk_size = 100 * 1024 * 1024
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(temp_fd)

    try:
        for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
            try:
                logger.info("Downloading file", url=url, attempt=attempt)
                await stream_to_file(url, temp_path, read_timeout, chunk_size)
                break
            except (httpx.ReadError, httpx.RemoteProtocolError) as e:
                if attempt == MAX_DOWNLOAD_ATTEMPTS:
                    logger.error(
                        "Download failed after all attempts",
                        url=url,
                        attempts=MAX_DOWNLOAD_ATTEMPTS,
                        error=str(e),
                    )
                    raise e
                logger.warning(
                    "Download attempt failed, retrying",
                    url=url,
                    attempt=attempt,
                    error=str(e),
                )
                await asyncio.sleep(2**attempt)
        logger.info("File downloaded successfully", url=url, path=temp_path)
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
