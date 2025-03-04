from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def daily_bucket(evaluator: MacroEvaluator, timeExp: exp.Expression):
    if evaluator.dialect == "duckdb":
        return exp.Anonymous(
            this="TIME_BUCKET",
            expressions=[
                exp.Interval(
                    this=exp.Literal(this=1, is_string=True),
                    unit=exp.Var(this="DAY"),
                ),
                timeExp,
            ],
        )
    return exp.Anonymous(
        this="toStartOfDay",
        expressions=[
            timeExp,
        ],
    )


@macro()
def weekly_bucket(evaluator: MacroEvaluator, timeExp: exp.Expression):
    if evaluator.dialect == "duckdb":
        return exp.Anonymous(
            this="TIME_BUCKET",
            expressions=[
                exp.Interval(
                    this=exp.Literal(this=1, is_string=True),
                    unit=exp.Var(this="WEEK"),
                ),
                timeExp,
            ],
        )
    return exp.Anonymous(
        this="toStartOfWeek",
        expressions=[
            timeExp,
        ],
    )
