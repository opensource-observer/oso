import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, TypedDict, Unpack

import cryo
import dlt
import polars as pl
import structlog
from dlt.destinations.adapters import bigquery_adapter
from oso_dagster.config import DagsterConfig
from web3 import Web3

logger = structlog.get_logger(__name__)


@dataclass(kw_only=True)
class CryoResourceConfig:
    primary_key: str | list[str]
    datatype: str
    rpc_url: str
    start_date: datetime
    partition_date: datetime
    partition_key: str


class CryoCollectKwargs(TypedDict):
    blocks: list[str]
    rpc: str
    output_format: Literal["polars"]


def cryo_resource_factory(global_config: DagsterConfig, config: CryoResourceConfig):
    block_range = find_block_range_from_date(config)
    cryo_config: CryoCollectKwargs = {
        "blocks": block_range,
        "rpc": config.rpc_url,
        "output_format": "polars",
    }
    datatype = config.datatype

    logger.info("Creating cryo resource", datatype=datatype, blocks=block_range)

    @dlt.resource(
        name=config.datatype,
        primary_key=config.primary_key,
        write_disposition="replace",
    )
    async def cryo_resource():
        resource_df, blocks_df = await collect_data(datatype, **cryo_config)
        resource_df = filter_data(resource_df, datatype)
        resource_df = enrich_data(resource_df, blocks_df)

        yield resource_df.to_arrow()

    if global_config.gcp_bigquery_enabled:
        bigquery_adapter(
            cryo_resource,
            partition=config.partition_key,
        )

    return cryo_resource


async def collect_data(
    datatype: str, **kwargs: Unpack[CryoCollectKwargs]
) -> tuple[pl.DataFrame, pl.DataFrame | None]:
    """Collects the main datatype and, if needed, the blocks data in parallel."""
    main_task = cryo.async_collect(
        datatype=datatype, columns=["all"], include_columns=["all"], **kwargs
    )
    if datatype != "blocks":
        blocks_task = cryo.async_collect(
            datatype="blocks",
            include_columns=["block_number", "timestamp"],
            **kwargs,
        )
        main_df, blocks_df = await asyncio.gather(main_task, blocks_task)
        assert isinstance(main_df, pl.DataFrame)
        assert isinstance(blocks_df, pl.DataFrame)
        return main_df, blocks_df

    main_df = await main_task
    assert isinstance(main_df, pl.DataFrame)
    return main_df, None


def enrich_data(
    resource_df: pl.DataFrame, blocks_df: pl.DataFrame | None
) -> pl.DataFrame:
    """Enriches the main dataframe with block timestamps if blocks data is provided."""
    df = resource_df
    if blocks_df is not None:
        assert isinstance(blocks_df, pl.DataFrame)
        blocks_df = blocks_df.rename({"timestamp": "block_timestamp"})
        df = df.join(blocks_df, on="block_number", how="left")

    timestamp_col = None
    if "block_timestamp" in df.columns:
        timestamp_col = "block_timestamp"
    elif "timestamp" in df.columns:
        timestamp_col = "timestamp"

    if timestamp_col:
        df = df.with_columns(pl.from_epoch(timestamp_col, time_unit="s").alias("dt"))

    return df


def filter_data(resource_df: pl.DataFrame, datatype: str):
    if datatype == "traces":
        resource_df = resource_df.filter(pl.col("action_type") != "reward")
    return resource_df


def find_block_range_from_date(config: CryoResourceConfig) -> list[str]:
    """Find the block range for a given day."""
    w3 = Web3(Web3.HTTPProvider(config.rpc_url))

    start_of_day = config.partition_date.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    start_of_next_day = start_of_day + timedelta(days=1)

    start_timestamp = int(start_of_day.timestamp())
    end_timestamp = int(start_of_next_day.timestamp())

    start_block = (
        _find_block_ge_timestamp(w3, start_timestamp)
        if config.start_date != config.partition_date
        else 0
    )  # Workaround because Ethereum start block has timestamp 0
    end_block = _find_block_ge_timestamp(w3, end_timestamp)

    return [f"{start_block}:{end_block}"]


def _find_block_ge_timestamp(w3: Web3, timestamp: int) -> int:
    """Finds the earliest block with a timestamp greater than or equal to the given timestamp."""
    low = 0
    high = w3.eth.block_number
    result_block = high

    while low <= high:
        mid = (low + high) // 2
        try:
            block_timestamp = w3.eth.get_block(mid).get("timestamp")

            if block_timestamp is None or block_timestamp < timestamp:
                low = mid + 1
            else:
                result_block = mid
                high = mid - 1
        except Exception:  # Handle cases where block doesn't exist
            high = mid - 1
    return result_block
