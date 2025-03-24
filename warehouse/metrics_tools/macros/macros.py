import typing as t

import sqlglot
from metrics_tools.definition import (
    PeerMetricDependencyRef,
    time_suffix,
    to_actual_table_name,
)
from metrics_tools.utils import exp_literal_to_py_literal
from sqlglot import expressions as exp
from sqlmesh.core.dialect import MacroVar, parse_one
from sqlmesh.core.macros import MacroEvaluator


def relative_window_sample_date(
    evaluator: MacroEvaluator,
    base: exp.Expression,
    window: exp.Expression,
    unit: str | exp.Expression,
    relative_index: exp.Expression,
):
    """Gets the rolling window sample date of a different table. For now this is
    quite explicit as opposed to using any real relationship between a related
    table. We calculate a relative window's sample date using the formula

    base + INTERVAL RELATIVE_INDEX UNIT

    Inherently, this won't, for now, work on custom unit types as the interval
    must be a valid thing to subtract from. Also note, the base should generally
    be the `@metrics_end` date.
    """
    if isinstance(unit, exp.Literal):
        unit = t.cast(str, unit.this)
    elif isinstance(unit, exp.Expression):
        transformed = evaluator.transform(unit)
        if not transformed:
            raise Exception("invalid window unit")
        if isinstance(transformed, list):
            unit = transformed[0].sql()
        else:
            if isinstance(transformed, exp.Literal):
                unit = t.cast(str, transformed.this)
            else:
                unit = transformed.sql()

    converted_relative_index = 0
    if isinstance(relative_index, exp.Literal):
        converted_relative_index = int(t.cast(int, relative_index.this))
    elif isinstance(relative_index, exp.Neg):
        converted_relative_index = int(relative_index.this.this) * -1
    if converted_relative_index == 0:
        return base
    window_int = int(evaluator.eval_expression(window))
    interval_delta_int = converted_relative_index * window_int
    interval_unit = exp.Var(this=unit)
    interval_delta = exp.Interval(
        this=exp.Literal(this=str(abs(interval_delta_int)), is_string=False),
        unit=interval_unit,
    )
    if converted_relative_index > 0:
        return exp.Add(this=base, expression=interval_delta)
    else:
        return exp.Sub(this=base, expression=interval_delta)


def time_aggregation_bucket(
    evaluator: MacroEvaluator, time_exp: exp.Expression, interval: str
):
    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")

    if interval == "over_all_time":
        return parse_one("CURRENT_DATE()")

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
                    this=exp.Literal(this="1", is_string=False),
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


def metrics_name(evaluator: MacroEvaluator, override: exp.Expression | str = ""):
    if override:
        if isinstance(override, str):
            override = exp.Literal(this=override, is_string=True)
    name = override
    if not name:
        name = exp.Literal(
            this=evaluator.locals.get("generated_metric_name"), is_string=True
        )
    rolling_window = evaluator.locals.get("rolling_window", "")
    rolling_unit = evaluator.locals.get("rolling_unit", "")
    time_aggregation = evaluator.locals.get("time_aggregation", "")
    suffix = time_suffix(time_aggregation, rolling_window, rolling_unit)
    if suffix:
        suffix = f"_{suffix}"

    return exp.Concat(
        expressions=[name, exp.Literal(this=suffix, is_string=True)],
        safe=False,
        coalesce=False,
    )


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
    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")
    time_aggregation_interval = evaluator.locals.get("time_aggregation")

    if time_aggregation_interval == "over_all_time":
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")

    if time_aggregation_interval:
        start_date = t.cast(
            exp.Expression,
            evaluator.transform(
                exp.StrToDate(
                    this=MacroVar(this="start_ds"),
                    format=exp.Literal(this="%Y-%m-%d", is_string=True),
                )
            ),
        )
        return evaluator.transform(
            time_aggregation_bucket(evaluator, start_date, time_aggregation_interval)
        )
    else:
        # We are documenting that devs do do date filtering with the `between`
        # operator so the metrics_end value is inclusive. This means that we
        # want to go back the rolling window - 1
        rolling_window = evaluator.locals.get("rolling_window")
        if rolling_window is None:
            raise Exception(
                "metrics_start used in a non metrics model. Model was not supplied a rolling_window"
            )
        else:
            rolling_window = t.cast(int, rolling_window)
            rolling_window = rolling_window - 1
        rolling_unit = evaluator.locals.get("rolling_unit", "")
        if rolling_unit not in ["day", "month", "year", "week", "quarter"]:
            raise Exception(
                f'Invalid use of metrics_start. Cannot use rolling_unit="{rolling_unit}"'
            )

        # Calculated rolling start
        rolling_start = exp.Sub(
            this=exp.Cast(
                this=exp.StrToDate(
                    this=MacroVar(this="end_ds"),
                    format=exp.Literal(this="%Y-%m-%d", is_string=True),
                ),
                to=exp.DataType(this=exp.DataType.Type.DATETIME),
                _type=exp.DataType(this=exp.DataType.Type.DATETIME),
            ),
            expression=exp.Interval(
                # The interval parameter should be a string or some dialects
                # have issues parsing
                this=exp.Literal(this=str(rolling_window), is_string=True),
                unit=exp.Var(this=rolling_unit.upper()),
            ),
        )
        return evaluator.transform(rolling_start)


def metrics_end(evaluator: MacroEvaluator, _data_type: t.Optional[str] = None):
    """This has different semantic meanings depending on the mode of the metric query"""

    if evaluator.runtime_stage in ["loading", "creating"]:
        return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")
    time_aggregation_interval = evaluator.locals.get("time_aggregation")

    if time_aggregation_interval == "over_all_time":
        return parse_one("CURRENT_DATE()")

    if time_aggregation_interval:
        to_interval = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
        }
        time_agg_end = exp.Add(
            this=exp.Cast(
                this=exp.StrToDate(
                    this=MacroVar(this="end_ds"),
                    format=exp.Literal(
                        this="%Y-%m-%d",
                        is_string=True,
                    ),
                ),
                to=exp.DataType(this=exp.DataType.Type.DATETIME),
                _type=exp.DataType(this=exp.DataType.Type.DATETIME),
            ),
            expression=exp.Interval(
                this=exp.Literal(this="1", is_string=True),
                unit=exp.Var(this=to_interval[time_aggregation_interval]),
            ),
        )
        end_date = t.cast(
            exp.Expression,
            time_agg_end,
        )
        return evaluator.transform(
            time_aggregation_bucket(evaluator, end_date, time_aggregation_interval)
        )
    return evaluator.transform(
        exp.StrToDate(
            this=MacroVar(this="end_ds"),
            format=exp.Literal(this="%Y-%m-%d", is_string=True),
        )
    )


def metrics_sample_interval_length(
    evaluator: MacroEvaluator,
    unit_exp: str | exp.Literal,
    start_exp: t.Optional[exp.Expression] = None,
    end_exp: t.Optional[exp.Expression] = None,
):
    """Uses start/end dates to calculate the interval length"""
    assert isinstance(
        unit_exp, (str, exp.Literal)
    ), "unit_exp must be a string or literal"
    if isinstance(unit_exp, exp.Literal):
        unit = exp.Var(this=unit_exp.this)
    else:
        unit = exp.Var(this=unit_exp.upper())
    if not start_exp:
        start = metrics_start(evaluator, "DATE")
        assert isinstance(start, exp.Expression), "start must be an expression"
        start_exp = start
    if not end_exp:
        end = metrics_end(evaluator, "DATE")
        assert isinstance(end, exp.Expression), "end must be an expression"
        end_exp = end
    return exp.DateDiff(
        this=end_exp,
        expression=start_exp,
        unit=unit,
    )


def metrics_entity_type_col(
    evaluator: MacroEvaluator,
    format_str: str,
    table_alias: exp.Expression | str | None = None,
    include_column_alias: exp.Expression | bool = False,
):
    names = []

    if isinstance(format_str, exp.Literal):
        format_str = format_str.this

    if table_alias:
        if isinstance(table_alias, (exp.TableAlias, exp.Literal, exp.Column)):
            if isinstance(table_alias.this, exp.Identifier):
                names.append(table_alias.this.this)
            else:
                names.append(table_alias.this)
        elif isinstance(table_alias, str):
            names.append(table_alias)
        else:
            names.append(table_alias.sql())
    column_name = format_str.format(
        entity_type=evaluator.locals.get("entity_type", "artifact")
    )
    names.append(column_name)
    column = sqlglot.to_column(f"{'.'.join(names)}", quoted=True)
    if include_column_alias:
        return column.as_(column_name)
    return column


def metrics_entity_type_alias(
    evaluator: MacroEvaluator, to_alias: exp.Expression, format_str: str
):
    if isinstance(format_str, exp.Literal):
        format_str = format_str.this
    alias_name = format_str.format(
        entity_type=evaluator.locals.get("entity_type", "artifact")
    )
    return exp.alias_(to_alias, alias_name)


def metrics_entity_type_table(evaluator: MacroEvaluator, format_str: str):
    """Turns a format string into a table name"""
    if isinstance(format_str, exp.Literal):
        format_str = format_str.this
    table_name = format_str.format(
        entity_type=evaluator.locals.get("entity_type", "artifact")
    )
    return sqlglot.to_table(table_name, quoted=True)


def metrics_peer_ref(
    evaluator: MacroEvaluator,
    name: str,
    *,
    entity_type: t.Optional[exp.Expression] = None,
    window: t.Optional[exp.Expression] = None,
    unit: t.Optional[exp.Expression] = None,
    time_aggregation: t.Optional[exp.Expression] = None,
):
    entity_type_val = (
        t.cast(str, exp_literal_to_py_literal(entity_type))
        if entity_type
        else evaluator.locals.get("entity_type", "")
    )
    window_val = int(exp_literal_to_py_literal(window)) if window else None
    unit_val = t.cast(str, exp_literal_to_py_literal(unit)) if unit else None
    time_aggregation_val = (
        t.cast(str, exp_literal_to_py_literal(time_aggregation))
        if time_aggregation
        else None
    )
    peer_db = t.cast(dict, evaluator.locals.get("$$peer_db"))
    peer_table_map = t.cast(dict, evaluator.locals.get("$$peer_table_map"))

    ref = PeerMetricDependencyRef(
        name=name,
        entity_type=entity_type_val,
        window=window_val,
        unit=unit_val,
        time_aggregation=time_aggregation_val,
    )
    return exp.to_table(f"{peer_db}.{to_actual_table_name(ref, peer_table_map)}")
