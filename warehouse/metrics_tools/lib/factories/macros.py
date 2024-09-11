import sqlglot
from sqlmesh.core.macros import MacroEvaluator
from sqlglot import expressions as exp
from .definition import time_suffix


def metric_name(evaluator: MacroEvaluator, override: str = ""):
    if override:
        if isinstance(override, exp.Literal):
            override = override.this
    name = override or evaluator.locals.get("generated_metric_name")
    rolling_window = evaluator.locals.get("rolling_window", "")
    rolling_unit = evaluator.locals.get("rolling_unit", "")
    time_aggregation = evaluator.locals.get("time_aggregation", "")
    suffix = time_suffix(time_aggregation, rolling_window, rolling_unit)

    return exp.Literal(this=f"{name}_{suffix}", is_string=True)


def entity_type_col(
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
