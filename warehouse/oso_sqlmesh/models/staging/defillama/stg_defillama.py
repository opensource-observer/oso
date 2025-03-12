import typing as t
from datetime import datetime

import orjson
import pandas as pd
from metrics_tools.source.rewrite import oso_source_for_pymodel
from oso_dagster.assets.defillama import defillama_chain_mappings
from sqlglot import exp
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model import ModelKindName


def parse_chain_tvl(protocol: str, chain_tvls_raw: str, start: datetime, end: datetime):
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
                        "chain": defillama_chain_mappings(chain),
                        "token": "",
                        "tvl": amount,
                        "event_type": "TVL",
                    }
                    series.append(event)
        except orjson.JSONDecodeError:
            return []
    return series


@model(
    name="oso.stg__defillama_tvl_events",
    is_sql=False,
    columns={
        "time": "TIMESTAMP",
        "slug": "VARCHAR",
        "protocol": "VARCHAR",
        "chain": "VARCHAR",
        "token": "VARCHAR",
        "tvl": "DOUBLE",
    },
    kind={
        "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        "time_column": "time",
        "batch_size": 7,
    },
    partitioned_by=("month(time)",),
)
def defillama_tvl_model(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    oso_source_rewrite: t.Optional[t.Dict[str, t.Any]] = None,
    **kwargs,
) -> t.Iterator[pd.DataFrame]:
    table = oso_source_for_pymodel(context, "bigquery.defillama.tvl")

    df = context.fetchdf(
        exp.select("slug", "chain_tvls")
        .from_(table)
        .where(
            exp.Between(
                this=exp.Cast(
                    this=exp.to_column("_dlt_load_id"),
                    to=exp.DataType(
                        this=exp.DataType.Type.DOUBLE,
                        nested=False,
                    ),
                ),
                low=exp.Literal(this=int(start.timestamp()), is_string=False),
                high=exp.Literal(this=int(end.timestamp()), is_string=False),
            )
        )
        .sql(dialect=context.engine_adapter.dialect)
    )

    if df.empty:
        yield from ()
        return

    result_rows = []
    for _, row in df.iterrows():
        slug = row["slug"]
        protocol_tvl_rows = parse_chain_tvl(slug, row["chain_tvls"], start, end)
        result_rows.extend(protocol_tvl_rows)

    if not result_rows:
        yield from ()
        return

    result = pd.DataFrame(
        result_rows,
        columns=["time", "slug", "protocol", "chain", "token", "tvl", "event_type"],
    )

    yield result[["time", "slug", "protocol", "chain", "token", "tvl"]]
