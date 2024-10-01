import typing as t

import sqlglot
from sqlglot import expressions as exp
from sqlmesh.core.dialect import MacroVar, parse_one
from sqlmesh.core.macros import MacroEvaluator

from .definition import time_suffix


def relative_window_sample_date(
    evaluator: MacroEvaluator,
    base: exp.Expression,
    window: exp.Expression,
    unit: exp.Expression,
    relative_index: int,
):
    """Gets the rolling window sample date of a different table. For now this is
    quite explicit as opposed to using any real relationship between a related
    table. We calculate a relative window's sample date using the formula

    base - INTERVAL RELATIVE_INDEX UNIT

    Inherently, this won't, for now, work on custom unit types.
    """
    if evaluator.runtime_stage in ["loading", "j"]:
        pass


def time_aggregation_bucket(
    evaluator: MacroEvaluator, time_exp: exp.Expression, interval: str
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
                    unit=exp.Var(this=rollup_to_interval[interval]),
                ),
                exp.Cast(
                    this=time_exp,
                    to=exp.DataType(this=exp.DataType.Type.DATE, nested=False),
                ),
            ],
        )
    elif evaluator.engine_adapter.dialect == "trino":
        rollup_to_interval = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
        }
        return exp.TimestampTrunc(
            this=time_exp,
            unit=exp.Literal(this=rollup_to_interval[interval], is_string=True),
        )
    rollup_to_clickhouse_function = {
        "daily": "toStartOfDay",
        "weekly": "toStartOfWeek",
        "monthly": "toStartOfMonth",
    }
    return exp.Anonymous(
        this=rollup_to_clickhouse_function[interval],
        expressions=[
            time_exp,
        ],
    )


def metrics_sample_date(
    evaluator: MacroEvaluator, time_exp: t.Optional[exp.Expression] = None
):
    """For the current metric, this provides the expected sample date that
    should be used on final result"""
    time_aggregation_interval = evaluator.locals.get("time_aggregation")
    if time_aggregation_interval:
        # return parse_one("STR_TO_DATE(@start_ds, '%Y-%m-%d)", dialect="clickhouse")
        if not time_exp:
            raise Exception(
                "metrics_sample_date must have a date input when used in a time_aggregation metric"
            )
        return evaluator.transform(
            time_aggregation_bucket(evaluator, time_exp, time_aggregation_interval)
        )
    return evaluator.transform(
        exp.StrToDate(
            this=MacroVar(this="end_ds"),
            format=exp.Literal(this="%Y-%m-%d", is_string=True),
        )
    )


def metrics_name(evaluator: MacroEvaluator, override: str = ""):
    if override:
        if isinstance(override, exp.Literal):
            override = override.this
    name = override or evaluator.locals.get("generated_metric_name")
    rolling_window = evaluator.locals.get("rolling_window", "")
    rolling_unit = evaluator.locals.get("rolling_unit", "")
    time_aggregation = evaluator.locals.get("time_aggregation", "")
    suffix = time_suffix(time_aggregation, rolling_window, rolling_unit)

    return exp.Literal(this=f"{name}_{suffix}", is_string=True)


def metrics_start(evaluator: MacroEvaluator, _data_type: t.Optional[str] = None):
    """This has different semantic meanings depending on the mode of the metric query

    * During `time_aggregation` mode:
        * This means the start of the interval as set by sqlmesh for doing the
          calculation. This is not intended as a rolling window. So for a cron that is handled monthly, this
    * During `rolling` mode:
        * This means the start of the rolling interval. This is derived
          by taking the end_ds provided by sqlmesh and calculating a
          trailing interval back {window} intervals of unit {unit}.
    """
    time_aggregation_interval = evaluator.locals.get("time_aggregation")
    if time_aggregation_interval:
        start_date = t.cast(
            exp.Expression,
            evaluator.transform(
                parse_one("STR_TO_DATE(@start_ds, '%Y-%m-%d')", dialect="clickhouse")
            ),
        )
        return evaluator.transform(
            time_aggregation_bucket(evaluator, start_date, time_aggregation_interval)
        )
    else:
        return evaluator.transform(
            parse_one(
                "STR_TO_DATE(@end_ds, '%Y-%m-%d') - INTERVAL @rolling_window DAY",
                dialect="clickhouse",
            )
        )


def metrics_end(evaluator: MacroEvaluator, _data_type: t.Optional[str] = None):
    """This has different semantic meanings depending on the mode of the metric query"""

    time_aggregation_interval = evaluator.locals.get("time_aggregation")
    if time_aggregation_interval:
        end_date = t.cast(
            exp.Expression,
            evaluator.transform(
                parse_one(
                    f"STR_TO_DATE(@end_ds, '%Y-%m-%d') + INTERVAL 1 {time_aggregation_interval}",
                    dialect="clickhouse",
                )
            ),
        )
        return evaluator.transform(
            time_aggregation_bucket(evaluator, end_date, time_aggregation_interval)
        )
    return evaluator.transform(
        parse_one("STR_TO_DATE(@end_ds, '%Y-%m-%d')", dialect="clickhouse")
    )


def metrics_entity_type_col(
    evaluator: MacroEvaluator,
    format_str: str,
    table_alias: exp.Expression | str | None = None,
):
    names = []

    if isinstance(format_str, exp.Literal):
        format_str = format_str.this

    if table_alias:
        if isinstance(table_alias, exp.TableAlias):
            names.append(table_alias.this)
        elif isinstance(table_alias, str):
            names.append(table_alias)
        elif isinstance(table_alias, exp.Literal):
            names.append(table_alias.this)
    column_name = format_str % evaluator.locals.get("entity_type", "artifact")
    names.append(column_name)
    return sqlglot.to_column(f"{'.'.join(names)}")
