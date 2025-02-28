import typing as t

from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def from_unix_timestamp(
    evaluator: MacroEvaluator,
    time_exp: exp.Expression,
    data_type: str = "TIMESTAMP",
):
    """Convert a unix epoch timestamp to a date or timestamp."""
    from sqlmesh.core.dialect import parse_one

    output_data_type = parse_one(
        data_type, dialect=t.cast(str, evaluator.dialect), into=exp.DataType
    )

    if evaluator.runtime_stage in ["loading", "creating"]:
        return exp.Cast(
            this=exp.Literal(this="1970-01-01", is_string=True),
            to=exp.DataType(this=output_data_type),
        )

    if evaluator.engine_adapter.dialect == "duckdb":
        timestamp_exp = exp.Anonymous(
            this="to_timestamp",
            expressions=[time_exp],
        )
    elif evaluator.engine_adapter.dialect == "trino":
        timestamp_exp = exp.Anonymous(
            this="from_unixtime",
            expressions=[time_exp],
        )
    else:
        raise NotImplementedError(
            f"from_unix_timestamp not implemented for {evaluator.engine_adapter.dialect}"
        )
    return exp.Cast(this=timestamp_exp, to=exp.DataType(this=output_data_type))
