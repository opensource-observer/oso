from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def time_aggregation_bucket(
    evaluator: MacroEvaluator, time_exp: exp.Expression, rollup: str
):
    from sqlmesh.core.dialect import parse_one

    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")
    if evaluator.engine_adapter.dialect == "duckdb":
        rollup_to_interval = {
            "daily": "DAY",
            "weekly": "WEEK",
            "monthly": "MONTH",
        }
        return exp.Anonymous(
            this="TIME_BUCKET",
            expressions=[
                exp.Interval(
                    this=exp.Literal(this=1, is_string=False),
                    unit=exp.Var(this=rollup_to_interval[rollup]),
                ),
                exp.Cast(
                    this=time_exp,
                    to=exp.DataType(this=exp.DataType.Type.DATE, nested=False),
                ),
            ],
        )
    rollup_to_clickhouse_function = {
        "daily": "toStartOfDay",
        "weekly": "toStartOfWeek",
        "monthly": "toStartOfMonth",
    }
    return exp.Anonymous(
        this=rollup_to_clickhouse_function[rollup],
        expressions=[
            time_exp,
        ],
    )
