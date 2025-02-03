from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def chain_name(evaluator: MacroEvaluator, chain: exp.Expression) -> exp.Expression:
    return exp.Case(
        ifs=[
            (exp.EQ(this=chain, expression=exp.Literal.string("op")), 
             exp.Literal.string("OPTIMISM")),
            (exp.EQ(this=chain, expression=exp.Literal.string("fraxtal")), 
             exp.Literal.string("FRAX")),
        ],
        default=exp.Upper(this=chain)
    )
