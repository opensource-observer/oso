import dlt
from scheduler.mq.handlers.ingestion.utils.download import download_to_temp
from scheduler.mq.handlers.ingestion.utils.readers import (
    FORMAT_READERS,
    FileFormat,
)


@dlt.resource(write_disposition="replace")
async def file_from_https(
    url: str,
    file_format: FileFormat,
    batch_size: int = 50000,
    timeout: int = 600,
):
    """Stream file from HTTPS and yield records."""
    async with download_to_temp(
        url, suffix=f".{file_format}", timeout=timeout
    ) as temp_path:
        reader = FORMAT_READERS[file_format]
        async for record in reader(temp_path, batch_size):
            yield record
