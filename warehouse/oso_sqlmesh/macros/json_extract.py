from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def json_extract_from_array(
    evaluator: MacroEvaluator,
    json_expression: exp.Expression,
    key: str,
):
    """Convert a unix epoch timestamp to a date or timestamp."""

    if evaluator.runtime_stage in ["loading"]:
        return exp.Array(this=[])

    if evaluator.engine_adapter.dialect == "duckdb":
        result = exp.JSONExtract(
            this=json_expression,
            expression=exp.Literal(this=key, is_string=True),
        )
    elif evaluator.engine_adapter.dialect == "trino":
        # We need to use json_query because the json_extract function doesn't
        # support arrays well through it's JSONPath implementation
        result = exp.JSONExtract(
            this=exp.JSONExtract(
                this=json_expression,
                # It's possible we will need to use lax here, but that will
                # require further testing
                expression=exp.Literal(this=f"strict {key}", is_string=True),
                option=exp.Var(this="WITHOUT ARRAY WRAPPER"),
                json_query=True,
            ),
            expression=exp.Literal(this="$", is_string=True),
        )
    else:
        raise NotImplementedError(
            f"from_unix_timestamp not implemented for {evaluator.engine_adapter.dialect}"
        )
    return exp.Cast(
        this=result,
        to=exp.DataType(
            this=exp.DataType.Type.ARRAY,
            expressions=[
                exp.DataType(
                    this=exp.DataType.Type.JSON,
                    nested=False,
                )
            ],
            nested=True,
        ),
    )
