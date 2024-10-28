import typing as t

from oso_dagster.cbt.utils.compare import is_same_sql
from sqlglot.optimizer.qualify import qualify
from sqlglot import exp
import sqlglot as sql
from sqlmesh.core.dialect import parse_one


def exp_literal_to_py_literal(glot_literal: exp.Expression) -> t.Any:
    # Don't error by default let it pass
    if not isinstance(glot_literal, exp.Literal):
        return glot_literal
    return glot_literal.this


def assert_same_sql(actual: exp.Expression | str, expected: exp.Expression | str):
    if isinstance(actual, str):
        actual = parse_one(actual)
    if isinstance(expected, str):
        expected = parse_one(expected)
    actual = qualify(actual)
    expected = qualify(expected)
    if not is_same_sql(actual, expected):
        assert parse_one(actual.sql()) == parse_one(expected.sql())
    else:
        print("SQL DIFF")
        diff = sql.diff(actual, expected)
        for d in diff:
            print(d)
        print(len(diff))
        assert is_same_sql(actual, expected)
