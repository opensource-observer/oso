from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.macros import MacroEvaluator

INTERVAL_CONVERSION: dict[str, tuple[int, str]] = {
    "daily": (1, "day"),
    "weekly": (1, "week"),
    "monthly": (1, "month"),
    "quarterly": (3, "month"),
    "biannually": (6, "month"),
    "yearly": (1, "year"),
    "day": (1, "day"),
    "week": (1, "week"),
    "month": (1, "month"),
    "quarter": (3, "month"),
    "biannual": (6, "month"),
    "year": (1, "year"),
}

@macro()
def time_aggregation_bucket(
    evaluator: MacroEvaluator, time_exp: exp.Expression, interval: str, offset: int = 0
):
    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")

    if interval == "over_all_time":
        return parse_one("CURRENT_DATE()")

    assert interval in INTERVAL_CONVERSION, f"Invalid interval type={interval}"

    current_interval = INTERVAL_CONVERSION[interval]

    if offset:
        total_offset = current_interval[0] * offset
        time_exp = exp.DateAdd(
            this=time_exp,
            expression=exp.Literal(this=str(total_offset), is_string=False),
            unit=exp.Var(this=current_interval[1].upper()),
        )

    if evaluator.engine_adapter.dialect == "duckdb":
        return exp.Anonymous(
            this="TIME_BUCKET",
            expressions=[
                exp.Interval(
                    this=exp.Literal(this=str(current_interval[0]), is_string=False),
                    unit=exp.Var(this=current_interval[1].upper()),
                ),
                exp.Cast(
                    this=time_exp,
                    to=exp.DataType(this=exp.DataType.Type.DATE, nested=False),
                ),
            ],
        )

    return exp.TimestampTrunc(
        this=time_exp,
        unit=exp.Literal(this=current_interval[1], is_string=True),
    )
