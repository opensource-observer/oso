import os
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiofiles
import httpx


@asynccontextmanager
async def download_to_temp(url: str, suffix: str, timeout: int) -> AsyncIterator[str]:
    """Stream download to temp disk, auto-cleanup on exit."""
    chunk_size = 100 * 1024 * 1024

    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(temp_fd)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async with aiofiles.open(temp_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        await f.write(chunk)
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
