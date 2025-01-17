import typing as t

import orjson
import pandas as pd
from metrics_mesh.macros.oso_source import oso_source_for_pymodel
from oso_dagster.assets.defillama import DEFI_LLAMA_PROTOCOLS, defi_llama_slug_to_name
from sqlglot import exp
from sqlmesh import ExecutionContext, model


def parse_chain_tvl(protocol: str, chain_tvls_raw: str):
    series = []
    if isinstance(chain_tvls_raw, str):
        try:
            chain_tvls = orjson.loads(chain_tvls_raw)
            keys = chain_tvls.keys()
            # Flatten the dictionary to a table
            for key in keys:
                tvl_history = chain_tvls[key]["tokens"]
                for entry in tvl_history:
                    tokens_values = entry["tokens"]
                    for token in tokens_values:
                        series.append(
                            [entry["date"], protocol, key, token, tokens_values[token]]
                        )
        except orjson.JSONDecodeError:
            return []
    return series


def defi_llama_tvl_model(protocol: str):
    @model(
        name=f"metrics.stg__{defi_llama_slug_to_name(protocol)}_tvl_events",
        is_sql=False,
        columns={
            "time": "INT64",
            "slug": "VARCHAR",
            "protocol": "VARCHAR",
            "chain": "VARCHAR",
            "token": "VARCHAR",
            "tvl": "FLOAT",
        },
    )
    def tvl_model(context: ExecutionContext, *args, **kwargs) -> pd.DataFrame:
        source_name = defi_llama_slug_to_name(protocol)
        # Run the query for the given protocol
        table = oso_source_for_pymodel(context, f"bigquery.defillama_tvl.{source_name}")
        df = context.fetchdf(
            exp.select("chain_tvls")
            .from_(table)
            .sql(dialect=context.engine_adapter.dialect)
        )
        # Parse the chain tvls
        result = pd.DataFrame(
            [
                row
                for chain_tvl in df["chain_tvls"].values
                for row in parse_chain_tvl("contango", chain_tvl)
            ],
            columns=["time", "protocol", "chain", "token", "tvl"],  # type: ignore
        )
        result["slug"] = protocol
        return result


def defi_llama_tvl_factory(protocols: t.List[str]):
    return [defi_llama_tvl_model(protocol) for protocol in protocols]


defi_llama_tvl_factory(DEFI_LLAMA_PROTOCOLS)
