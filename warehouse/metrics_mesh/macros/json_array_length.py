from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def json_array_length(
    evaluator: MacroEvaluator,
    array_expression: exp.Expression,
):
    """Convert a unix epoch timestamp to a date or timestamp."""

    if evaluator.runtime_stage in ["loading"]:
        return exp.ArraySize(this=array_expression)

    if evaluator.engine_adapter.dialect == "duckdb":
        return exp.ArraySize(this=array_expression)
    elif evaluator.engine_adapter.dialect == "trino":
        return exp.Anonymous(this="json_array_length", expressions=[array_expression])
    else:
        raise NotImplementedError(
            f"json_array_length not implemented for {evaluator.engine_adapter.dialect}"
        )
