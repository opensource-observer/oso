from typing import AsyncIterator, Callable, Literal

import pandas as pd
import pyarrow.parquet as pq

FileFormat = Literal["parquet", "csv", "json"]


async def read_parquet_batches(path: str, batch_size: int) -> AsyncIterator[dict]:
    """Stream parquet from disk in batches."""
    parquet_file = pq.ParquetFile(path)
    for batch in parquet_file.iter_batches(batch_size=batch_size):
        for record in batch.to_pylist():
            yield record


async def read_csv_batches(path: str, batch_size: int) -> AsyncIterator[dict]:
    """Stream CSV from disk."""
    for chunk in pd.read_csv(path, chunksize=batch_size):
        for record in chunk.to_dict(orient="records"):
            yield record


async def read_json_batches(path: str, _batch_size: int) -> AsyncIterator[dict]:
    """Read JSON from disk."""
    df = pd.read_json(path)
    for record in df.to_dict(orient="records"):
        yield record


FORMAT_READERS: dict[FileFormat, Callable[[str, int], AsyncIterator[dict]]] = {
    "parquet": read_parquet_batches,
    "csv": read_csv_batches,
    "json": read_json_batches,
}
