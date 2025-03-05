from oso_dagster.assets.defillama import DEFILLAMA_PROTOCOLS, defillama_slug_to_name
from sqlglot import exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def unioned_defillama_tvl_events(evaluator: MacroEvaluator):
    """Unions all of the defi llama staging models for use in a cte"""
    return exp.union(
        *[
            exp.select("*").from_(
                f"oso.stg__{defillama_slug_to_name(protocol)}_tvl_events"
            )
            for protocol in DEFILLAMA_PROTOCOLS
        ],
        distinct=False,
    )
