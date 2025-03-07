from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def chain_name(evaluator: MacroEvaluator, chain: exp.Expression):
    """Standardizes chain names across models."""
    return exp.Upper(
        this=exp.Case(
            ifs=[
                exp.If(
                    this=exp.EQ(this=chain, expression=exp.Literal.string("op")),
                    true=exp.Literal.string("optimism"),
                ),
                exp.If(
                    this=exp.EQ(this=chain, expression=exp.Literal.string("fraxtal")),
                    true=exp.Literal.string("frax"),
                ),
            ],
            default=chain,
        )
    )
