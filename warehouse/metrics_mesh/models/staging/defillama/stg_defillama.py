import typing as t
from datetime import datetime

import orjson
import pandas as pd
from metrics_tools.source.rewrite import oso_source_for_pymodel
from oso_dagster.assets.defillama import DEFILLAMA_PROTOCOLS, defillama_slug_to_name
from sqlglot import exp
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model import ModelKindName


def parse_chain_tvl(protocol: str, chain_tvls_raw: str, start: datetime, end: datetime):
    series = []
    if isinstance(chain_tvls_raw, str):
        try:
            chain_tvls = orjson.loads(chain_tvls_raw)
            chains = chain_tvls.keys()
            # Flatten the dictionary to a table
            for chain in chains:
                tvl_history = chain_tvls[chain]["tokens"]
                for entry in tvl_history:
                    # Skip entries outside the time range
                    if (
                        entry["date"] < start.timestamp()
                        or entry["date"] > end.timestamp()
                    ):
                        continue
                    tokens_values = entry["tokens"]
                    for token in tokens_values:
                        series.append(
                            [
                                pd.Timestamp(entry["date"], unit="s"),
                                protocol,
                                chain,
                                token,
                                tokens_values[token],
                            ]
                        )
        except orjson.JSONDecodeError:
            return []
    return series


def defillama_tvl_model(protocol: str):
    @model(
        name=f"metrics.stg__{defillama_slug_to_name(protocol)}_tvl_events",
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
    def tvl_model(
        context: ExecutionContext, start: datetime, end: datetime, *args, **kwargs
    ) -> t.Iterator[pd.DataFrame]:
        source_name = defillama_slug_to_name(protocol)
        # Run the query for the given protocol
        table = oso_source_for_pymodel(context, f"bigquery.defillama_tvl.{source_name}")
        df = context.fetchdf(
            exp.select("chain_tvls")
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
        # Parse the chain tvls
        result = pd.DataFrame(
            [
                row
                for chain_tvl in df["chain_tvls"].values
                for row in parse_chain_tvl(protocol, chain_tvl, start, end)
            ],
            columns=["time", "protocol", "chain", "token", "tvl"],  # type: ignore
        )
        if result.empty:
            yield from ()
            return
        result["slug"] = protocol
        # Reorder columns for correct response (possibly, this is a bug with
        # sqlmesh as dictionary order is not guaranteed)
        yield t.cast(
            pd.DataFrame, result[["time", "slug", "protocol", "chain", "token", "tvl"]]
        )


def defillama_tvl_factory(protocols: t.List[str]):
    return [defillama_tvl_model(protocol) for protocol in protocols]


defillama_tvl_factory(DEFILLAMA_PROTOCOLS)
