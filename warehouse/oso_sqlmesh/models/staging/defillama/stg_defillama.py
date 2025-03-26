import typing as t

import pandas as pd
from metrics_tools.source.rewrite import oso_source_for_pymodel
from sqlglot import exp
from sqlmesh import ExecutionContext, model


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
    kind="full",
    variables={
        "chunk_size": 500000,
    },
    partitioned_by=("month(time)",),
)
def defillama_tvl_model(
    context: ExecutionContext,
    oso_source_rewrite: t.Optional[t.Dict[str, t.Any]] = None,
    **kwargs,
) -> t.Generator[pd.DataFrame, None, None]:
    chunk_size = t.cast(int, context.var("chunk_size"))

    table = oso_source_for_pymodel(context, "bigquery.defillama.tvl_events")

    query = (
        exp.select(
            "time", "slug", "protocol", "parent_protocol", "chain", "token", "tvl"
        )
        .from_(table)
        .sql(dialect=context.engine_adapter.dialect)
    )

    df = context.fetchdf(query)

    if df.empty:
        yield from ()
        return

    if not pd.api.types.is_datetime64_any_dtype(df["time"]):
        df["time"] = pd.to_datetime(df["time"])

    yield from chunk_dataframe(df, chunk_size)
