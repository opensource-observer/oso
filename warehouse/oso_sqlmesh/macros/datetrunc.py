"""
Not sure why by `date_trunc` does not allow us to set the date part via a macro
variable in sqlmesh.

This is a workaround to allow us to set the date part via a macro variable
"""

from sqlglot import exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def datetrunc(evaluator: MacroEvaluator, date_part: exp.Expression, date_exp: exp.Expression):
    """Truncate a date to the specified date part."""

    date_part_str = evaluator.eval_expression(date_part)

    return exp.DateTrunc(
        unit=exp.Literal(this=date_part_str, is_string=True),
        this=date_exp,
    )