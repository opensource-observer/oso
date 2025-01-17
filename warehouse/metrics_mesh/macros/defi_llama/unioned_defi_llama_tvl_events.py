from oso_dagster.assets.defillama import DEFI_LLAMA_PROTOCOLS, defi_llama_slug_to_name
from sqlglot import exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def unioned_defi_llama_tvl_events(evaluator: MacroEvaluator):
    return exp.union(
        *[
            exp.select("*").from_(
                f"metrics.stg__{defi_llama_slug_to_name(protocol)}_tvl_events"
            )
            for protocol in DEFI_LLAMA_PROTOCOLS
        ],
        distinct=False,
    )
