from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def chain_name(
    evaluator: MacroEvaluator,
    chain: exp.Expression
):
    """Standardizes chain names across models."""
    if exp.Literal.string("op") == chain:
        chain = exp.Literal.string("optimism")
    elif exp.Literal.string("fraxtal") == chain:
        chain = exp.Literal.string("frax")
    return exp.Upper(this=chain)