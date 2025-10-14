from datetime import datetime, timedelta

from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.dialect import MacroFunc
from sqlmesh.core.macros import MacroEvaluator


@macro()
def extended_date_spine(
    evaluator: MacroEvaluator,
    interval: exp.Expression,
    start_ds: str,
    end_ds: str,
    minimum_days: int,
):
    """Date spine that supports larger intervals and offsetting."""
    # We assume the start_ds and end_ds are in the format 'YYYY-MM-DD'
    # Parse them to python dates

    start = datetime.strptime(start_ds, "%Y-%m-%d")
    end = datetime.strptime(end_ds, "%Y-%m-%d")

    minimum_start = end - timedelta(days=minimum_days)
    if start > minimum_start:
        start = minimum_start

    return MacroFunc(
        this=exp.Anonymous(
            this="date_spine",
            expressions=[
                interval,
                exp.Literal.string(start.strftime("%Y-%m-%d")),
                exp.Literal.string(end.strftime("%Y-%m-%d")),
            ],
        )
    )
