import typing as t

from sqlglot import exp
from sqlmesh.core.dialect import parse


def exp_literal_to_py_literal(glot_literal: exp.Expression) -> t.Any:
    # Don't error by default let it pass
    if not isinstance(glot_literal, exp.Literal):
        return glot_literal
    return glot_literal.this


def str_or_expressions(query: str | t.List[exp.Expression]) -> t.List[exp.Expression]:
    if not isinstance(query, list):
        return parse(query)
    return query
