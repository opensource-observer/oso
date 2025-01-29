import typing as t

import orjson
import pandas as pd
from metrics_tools.source.rewrite import oso_source_for_pymodel
from oso_dagster.assets.defillama import DEFILLAMA_PROTOCOLS, defillama_slug_to_name
from sqlglot import exp
from sqlmesh import ExecutionContext, model


def parse_chain_tvl(protocol: str, chain_tvls_raw: str):
    series = []
    if isinstance(chain_tvls_raw, str):
        try:
            chain_tvls = orjson.loads(chain_tvls_raw)
            chains = chain_tvls.keys()
            # Flatten the dictionary to a table
            for chain in chains:
                tvl_history = chain_tvls[chain]["tokens"]
                for entry in tvl_history:
                    tokens_values = entry["tokens"]
                    for token in tokens_values:
                        series.append(
                            [
                                entry["date"],
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
            "time": "INT64",
            "slug": "VARCHAR",
            "protocol": "VARCHAR",
            "chain": "VARCHAR",
            "token": "VARCHAR",
            "tvl": "DOUBLE",
        },
    )
    def tvl_model(
        context: ExecutionContext, *args, **kwargs
    ) -> t.Iterator[pd.DataFrame]:
        source_name = defillama_slug_to_name(protocol)
        # Run the query for the given protocol
        table = oso_source_for_pymodel(context, f"bigquery.defillama_tvl.{source_name}")
        df = context.fetchdf(
            exp.select("chain_tvls")
            .from_(table)
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
                for row in parse_chain_tvl(protocol, chain_tvl)
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
