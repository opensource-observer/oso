from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator
from sqlglot import expressions as exp


@macro()
def oso_id(evaluator: MacroEvaluator, *args: exp.Expression):
    sha = exp.SHA2(
        this=exp.Concat(expressions=args, safe=True, coalesce=False),
        length=exp.Literal(this=256, is_string=False),
    )
    if evaluator.runtime_stage in ["loading", "creating"]:
        return exp.Literal(this="", is_string=True)
    if evaluator.engine_adapter.dialect == "duckdb":
        return sha
    return exp.ToBase64(this=sha)
