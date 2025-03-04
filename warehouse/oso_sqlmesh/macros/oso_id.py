from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def oso_id(evaluator: MacroEvaluator, *args: exp.Expression):
    if evaluator.runtime_stage in ["loading", "creating"]:
        return exp.Literal(this="someid", is_string=True)
    concatenated = exp.Concat(expressions=args, safe=True, coalesce=False)
    if evaluator.engine_adapter.dialect == "trino":
        # Trino's SHA256 function only accepts type `varbinary`. So we convert
        # the varchar to varbinary with trino's to_utf8.
        concatenated = exp.Anonymous(this="to_utf8", expressions=[concatenated])
    sha = exp.SHA2(
        this=concatenated,
        length=exp.Literal(this=256, is_string=False),
    )
    if evaluator.runtime_stage in ["loading", "creating"]:
        return exp.Literal(this="", is_string=True)
    if evaluator.engine_adapter.dialect == "duckdb":
        return sha
    return exp.ToBase64(this=sha)
