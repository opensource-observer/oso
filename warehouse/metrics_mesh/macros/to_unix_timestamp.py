from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def str_to_unix_timestamp(
    evaluator: MacroEvaluator,
    time_exp: exp.Expression,
):
    from sqlmesh.core.dialect import parse_one

    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("1::Uint32", dialect="clickhouse")

    if evaluator.engine_adapter.dialect == "duckdb":
        return exp.TimeToUnix(
            this=exp.StrToTime(
                this=time_exp,
                format=exp.Array(
                    expressions=[exp.Literal(this="%Y-%m-%d", is_string=True)]
                ),
            )
        )
    return exp.Anonymous(
        this="toUnixTimestamp",
        expressions=[time_exp],
    )
