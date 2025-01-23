import typing as t

from sqlglot import exp
from sqlmesh.core.dialect import parse, parse_one


def coerce_to_column(column: str | exp.Expression) -> exp.Expression:
    if isinstance(column, str):
        return exp.to_column(column)
    elif isinstance(column, exp.Expression):
        return column
    raise ValueError(f"Invalid column type: {column}")


def coerce_to_table(table: str | exp.Expression) -> exp.Expression:
    if isinstance(table, str):
        return exp.to_table(table)
    elif isinstance(table, exp.Expression):
        return table
    raise ValueError(f"Invalid table type: {table}")


def coerce_to_expression(
    val: exp.ExpOrStr, coerce_type: exp.IntoType, dialect: t.Optional[str] = None
) -> exp.Expression:
    if isinstance(val, exp.Expression):
        return val
    elif isinstance(val, str):
        return parse_one(val, dialect=dialect, into=coerce_type)
    raise ValueError(f"Invalid value type: {val}")


def literal_or_expression(val: exp.ExpOrStr | int | float) -> exp.Expression:
    if isinstance(val, exp.Expression):
        return val
    elif isinstance(val, str):
        return exp.Literal(this=val, is_string=True)
    else:
        return exp.Literal(this=val, is_string=False)


def exp_literal_to_py_literal(glot_literal: exp.Expression) -> t.Any:
    # Don't error by default let it pass
    if not isinstance(glot_literal, exp.Literal):
        return glot_literal
    return glot_literal.this


def str_or_expressions(query: str | t.List[exp.Expression]) -> t.List[exp.Expression]:
    if not isinstance(query, list):
        return parse(query)
    return query
