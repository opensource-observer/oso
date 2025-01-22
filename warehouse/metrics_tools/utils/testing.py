import contextlib
import typing as t

import duckdb
import sqlglot as sql
from oso_dagster.cbt.utils.compare import is_same_sql
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlmesh.core.context import ExecutionContext
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter

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


def create_test_context(conn: t.Optional[duckdb.DuckDBPyConnection] = None):
    if not conn:
        conn = duckdb.connect(":memory:")

    def connection_factory():
        return conn

    engine_adapter = DuckDBEngineAdapter(connection_factory)
    context = ExecutionContext(engine_adapter, {})
    return context
