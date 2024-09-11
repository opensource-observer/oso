from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator
from sqlglot import expressions as exp


@macro()
def oso_id(_evaluator: MacroEvaluator, *args: exp.Expression):
    return exp.ToBase64(
        this=exp.SHA2(
            this=exp.Concat(expressions=args, safe=True, coalesce=False),
            length=exp.Literal(this=256, is_string=False),
        )
    )
