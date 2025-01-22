import typing as t

from sqlglot import exp
from sqlmesh.core.dialect import parse


def coerce_to_column(column: str | exp.Expression) -> exp.Expression:
    if isinstance(column, str):
        return exp.to_column(column)
    elif isinstance(column, exp.Expression):
        return column
    raise ValueError(f"Invalid column type: {column}")


def exp_literal_to_py_literal(glot_literal: exp.Expression) -> t.Any:
    # Don't error by default let it pass
    if not isinstance(glot_literal, exp.Literal):
        return glot_literal
    return glot_literal.this


def str_or_expressions(query: str | t.List[exp.Expression]) -> t.List[exp.Expression]:
    if not isinstance(query, list):
        return parse(query)
    return query
