from sqlmesh import macro
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.macros import MacroEvaluator


@macro()
def unioned_defillama_tvl_events(evaluator: MacroEvaluator):
    """Unions all of the defi llama staging models for use in a cte"""
    return parse_one("select 1 from limit")
