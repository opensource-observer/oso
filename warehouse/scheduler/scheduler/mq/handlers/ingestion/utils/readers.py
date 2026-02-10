import csv
import json
from typing import AsyncIterator, Callable, Literal

import aiofiles
import pyarrow.parquet as pq

FileFormat = Literal["parquet", "csv", "json"]


async def read_parquet_batches(path: str, batch_size: int) -> AsyncIterator[dict]:
    """Stream parquet from disk in batches."""
    parquet_file = pq.ParquetFile(path)
    for batch in parquet_file.iter_batches(batch_size=batch_size):
        for record in batch.to_pandas().to_dict(orient="records"):
            yield record


async def read_csv_batches(path: str, _batch_size: int) -> AsyncIterator[dict]:
    """Stream CSV from disk."""
    async with aiofiles.open(path, "r") as f:
        content = await f.read()

    reader = csv.DictReader(content.splitlines())
    for row in reader:
        yield row


async def read_json_batches(path: str, _batch_size: int) -> AsyncIterator[dict]:
    """Stream JSON from disk."""
    async with aiofiles.open(path, "r") as f:
        content = await f.read()

    data = json.loads(content)
    if isinstance(data, list):
        for record in data:
            yield record
    else:
        yield data


FORMAT_READERS: dict[FileFormat, Callable[[str, int], AsyncIterator[dict]]] = {
    "parquet": read_parquet_batches,
    "csv": read_csv_batches,
    "json": read_json_batches,
}
