import typing as t
from datetime import datetime

import orjson
import pandas as pd
from metrics_tools.models import constants
from metrics_tools.source.rewrite import oso_source_for_pymodel
from oso_dagster.assets.defillama import defillama_chain_mappings
from sqlglot import exp
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model import ModelKindName


def parse_chain_tvl(
    protocol: str,
    parent_protocol: str,
    chain_tvls_raw: str,
    start: datetime,
    end: datetime,
):
    """
    Extract aggregated TVL events from the chainTvls field.
    For each chain, each event is expected to have a date and a totalLiquidityUSD value.
    """
    series = []
    if isinstance(chain_tvls_raw, str):
        try:
            chain_tvls = orjson.loads(chain_tvls_raw)
            chains = chain_tvls.keys()
            # Flatten the dictionary to a table
            for chain in chains:
                tvl_history = chain_tvls[chain]["tvl"]
                if not tvl_history:
                    continue
                for entry in tvl_history:
                    # Skip entries outside the time range
                    if (
                        entry["date"] < start.timestamp()
                        or entry["date"] > end.timestamp()
                    ):
                        continue
                    amount = float(entry["totalLiquidityUSD"])
                    event = {
                        "time": pd.Timestamp(entry["date"], unit="s"),
                        "slug": protocol,
                        "protocol": protocol,
                        "parent_protocol": parent_protocol,
                        "chain": defillama_chain_mappings(chain),
                        "token": "USD",
                        "tvl": amount,
                        "event_type": "TVL",
                    }
                    series.append(event)
        except orjson.JSONDecodeError:
            return []
    return series


def chunk_dataframe(
    df: pd.DataFrame, chunk_size: int = 100
) -> t.Generator[pd.DataFrame, None, None]:
    """
    Split a dataframe into chunks of specified size.
    """
    num_chunks = (len(df) + chunk_size - 1) // chunk_size

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(df))
        yield df.iloc[start_idx:end_idx].copy()


@model(
    name="oso.stg__defillama_tvl_events",
    is_sql=False,
    columns={
        "time": "TIMESTAMP",
        "slug": "VARCHAR",
        "protocol": "VARCHAR",
        "parent_protocol": "VARCHAR",
        "chain": "VARCHAR",
        "token": "VARCHAR",
        "tvl": "DOUBLE",
    },
    kind={
        "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        "time_column": "time",
        "batch_size": 365,
    },
    variables={
        "chunk_size": 100,
    },
    partitioned_by=("month(time)",),
    start=constants.defillama_incremental_start,
)
def defillama_tvl_model(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    oso_source_rewrite: t.Optional[t.Dict[str, t.Any]] = None,
    **kwargs,
) -> t.Generator[pd.DataFrame, None, None]:
    chunk_size = t.cast(int, context.var("chunk_size"))
    table = oso_source_for_pymodel(context, "bigquery.defillama.tvl")

    df = context.fetchdf(
        exp.select("slug", "parent_protocol", "chain_tvls")
        .from_(table)
        .sql(dialect=context.engine_adapter.dialect)
    )

    if df.empty:
        yield from ()
        return

    result_rows = []
    for _, row in df.iterrows():
        slug = str(row["slug"])
        parent_protocol = str(row["parent_protocol"])
        if parent_protocol:
            parent_protocol = parent_protocol.replace("parent#", "")
        chain_tvls = str(row["chain_tvls"])
        protocol_tvl_rows = parse_chain_tvl(
            slug, parent_protocol, chain_tvls, start, end
        )
        result_rows.extend(protocol_tvl_rows)

    if not result_rows:
        yield from ()
        return

    result = pd.DataFrame(
        result_rows,
        columns=pd.Index(
            [
                "time",
                "slug",
                "protocol",
                "parent_protocol",
                "chain",
                "token",
                "tvl",
                "event_type",
            ]
        ),
    )

    filtered_result = result.loc[
        :,
        ["time", "slug", "protocol", "parent_protocol", "chain", "token", "tvl"],
    ]

    yield from chunk_dataframe(filtered_result, chunk_size)
