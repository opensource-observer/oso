# The worker initialization
import abc
from graphql import ExecutionContext
import pandas as pd
import typing as t
import duckdb
from datetime import datetime
from sqlglot import exp
from dask.distributed import WorkerPlugin, Worker


class DuckDBWorkerInterface(abc.ABC):
    def fetchdf(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("fetchdf not implemented")


class MetricsWorkerPlugin(WorkerPlugin):
    def __init__(self, duckdb_path: str):
        self._duckdb_path = duckdb_path
        self._conn = None

    def setup(self, worker: Worker):
        self._conn = duckdb.connect(self._duckdb_path)

        # Connect to iceberg if this is a remote worker
        self._conn.sql(
            """
        INSTALL iceberg;
        LOAD iceberg;
                    
        CREATE SECRET secret1 (
            TYPE GCS,
            PROVIDER CREDENTIAL_CHAIN
        )
        CREATE SCHEMA IF NOT EXISTS sources;
        CREATE TABLE IF NOT EXISTS sources.cache_status (
            table_name VARCHAR PRIMARY KEY, 
            version VARCHAR, 
            is_locked BOOLEAN
        );
        """
        )

    def teardown(self, worker: Worker):
        if self._conn:
            self._conn.close()

    @property
    def connection(self):
        assert self._conn is not None
        return self._conn

    def wait_for_cache(self, table: str):
        """Checks if a table is cached in the local duckdb"""
        self.connection.sql(
            f"""
            SELECT * FROM {table}
        """
        )


def batch_metrics_query(
    query: exp.Expression,
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
):
    """Yield batches of dataframes"""
    pass
