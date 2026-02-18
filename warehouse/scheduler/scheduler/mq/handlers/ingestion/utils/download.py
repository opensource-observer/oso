import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiofiles
import httpx

MAX_DOWNLOAD_ATTEMPTS = 3


async def stream_to_file(
    url: str, dest: str, read_timeout: int, chunk_size: int
) -> None:
    """Stream download to file with httpx."""
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
                await stream_to_file(url, temp_path, read_timeout, chunk_size)
                break
            except (httpx.ReadError, httpx.RemoteProtocolError) as e:
                if attempt == MAX_DOWNLOAD_ATTEMPTS:
                    raise e
                await asyncio.sleep(2**attempt)
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
