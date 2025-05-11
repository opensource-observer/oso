from metrics_tools.utils.glot import exp_literal_to_py_literal
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.dialect import MacroFunc, MacroVar, parse_one
from sqlmesh.core.macros import MacroEvaluator

INTERVAL_CONVERSION: dict[str, str] = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
    "quarterly": "month",
    "biannually": "month",
    "yearly": "year",
    "day": "day",
    "week": "week",
    "month": "month",
    "quarter": "month",
    "biannual": "month",
    "year": "year",
}


@macro()
def extended_date_spine(
    evaluator: MacroEvaluator,
    interval: exp.Expression,
    start: exp.Expression,
    end: exp.Expression,
):
    """Date spine that supports larger intervals and offsetting."""
    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")

    if isinstance(interval, exp.Literal):
        interval_str = exp_literal_to_py_literal(interval)
    else:
        raise ValueError(f"Unexpected interval input: {interval}")

    current_interval = INTERVAL_CONVERSION[interval_str]

    return MacroFunc(
        this=exp.Anonymous(
            this="date_spine",
            expressions=[
                MacroVar(this=current_interval),
                start,
                end,
            ],
        )
    )
