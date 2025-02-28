import contextlib
import os
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


def load_timeseries_metrics(metrics_mesh_dir: str):
    global ENABLE_TIMESERIES_DEBUG

    import importlib.util

    ENABLE_TIMESERIES_DEBUG = True

    from metrics_tools.factory.factory import GLOBAL_TIMESERIES_METRICS

    factory_path = os.path.join(metrics_mesh_dir, "models/metrics_factories.py")

    # Run the metrics factory in the sqlmesh project. This uses a single default
    # location for now.
    spec = importlib.util.spec_from_file_location(
        "metrics_mesh.metrics_factories", factory_path
    )
    assert (
        spec is not None
    ), f"Could not find metrics factory file at {metrics_mesh_dir}/models/metrics_factories.py"
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return GLOBAL_TIMESERIES_METRICS[factory_path]


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
