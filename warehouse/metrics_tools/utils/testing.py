import contextlib
import duckdb
from sqlglot.optimizer.qualify import qualify
import sqlglot as sql
from sqlglot import exp
from sqlmesh.core.dialect import parse_one
from oso_dagster.cbt.utils.compare import is_same_sql


ENABLE_TIMESERIES_DEBUG = False


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


@contextlib.contextmanager
def duckdb_df_context(connection: duckdb.DuckDBPyConnection, query: str):
    yield connection.sql(query).df()
