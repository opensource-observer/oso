from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator
from sqlglot import expressions as exp


@macro()
def day_bucket(evaluator: MacroEvaluator, timeExp: exp.Expression):
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
