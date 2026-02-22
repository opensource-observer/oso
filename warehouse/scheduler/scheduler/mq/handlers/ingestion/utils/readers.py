from typing import AsyncIterator, Callable, Literal

import pandas as pd
import pyarrow.parquet as pq
import structlog

logger = structlog.get_logger(__name__)

FileFormat = Literal["parquet", "csv", "json"]


async def read_parquet_batches(path: str, batch_size: int) -> AsyncIterator[list[dict]]:
    """Stream parquet from disk in batches."""
    logger.info("Reading parquet file", path=path, batch_size=batch_size)
    total_rows = 0
    parquet_file = pq.ParquetFile(path)
    for batch_num, batch in enumerate(parquet_file.iter_batches(batch_size=batch_size)):
        records = batch.to_pylist()
        logger.debug(
            "Parquet batch read", path=path, batch=batch_num, rows=len(records)
        )
        yield records
        total_rows += len(records)
    logger.info("Parquet file read complete", path=path, total_rows=total_rows)


async def read_csv_batches(path: str, batch_size: int) -> AsyncIterator[list[dict]]:
    """Stream CSV from disk."""
    logger.info("Reading CSV file", path=path, batch_size=batch_size)
    total_rows = 0
    for batch_num, chunk in enumerate(pd.read_csv(path, chunksize=batch_size)):
        records = chunk.to_dict(orient="records")
        logger.debug("CSV batch read", path=path, batch=batch_num, rows=len(records))
        yield records
        total_rows += len(records)
    logger.info("CSV file read complete", path=path, total_rows=total_rows)


async def read_json_batches(path: str, _batch_size: int) -> AsyncIterator[list[dict]]:
    """Read JSON from disk."""
    logger.info("Reading JSON file", path=path)
    df = pd.read_json(path)
    total_rows = len(df)
    yield df.to_dict(orient="records")
    logger.info("JSON file read complete", path=path, total_rows=total_rows)


FORMAT_READERS: dict[FileFormat, Callable[[str, int], AsyncIterator[list[dict]]]] = {
    "parquet": read_parquet_batches,
    "csv": read_csv_batches,
    "json": read_json_batches,
}
