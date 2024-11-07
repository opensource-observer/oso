# The worker initialization
import abc
import pandas as pd
import typing as t
import duckdb
from sqlglot import exp
from dask.distributed import WorkerPlugin, Worker

# from pyiceberg.catalog import load_catalog


class DuckDBWorkerInterface(abc.ABC):
    def fetchdf(self, query: str) -> pd.DataFrame:
        raise NotImplementedError("fetchdf not implemented")


class MetricsWorkerPlugin(WorkerPlugin):
    def __init__(self, gcs_key_id: str, gcs_secret: str, duckdb_path: str):
        self._gcs_key_id = gcs_key_id
        self._gcs_secret = gcs_secret
        self._duckdb_path = duckdb_path
        self._conn = None
        self._cache_status: t.Dict[str, str] = {}

    def setup(self, worker: Worker):
        self._conn = duckdb.connect(self._duckdb_path)

        # Connect to iceberg if this is a remote worker
        worker.log_event("info", "what")
        sql = f"""
        INSTALL iceberg;
        LOAD iceberg;
                    
        CREATE SECRET secret1 (
            TYPE GCS,
            KEY_ID '{self._gcs_key_id}',
            SECRET '{self._gcs_secret}'
        );
        """
        self._conn.sql(sql)

    def teardown(self, worker: Worker):
        if self._conn:
            self._conn.close()

    @property
    def connection(self):
        assert self._conn is not None
        return self._conn

    def get_for_cache(
        self,
        table_ref_name: str,
        table_actual_name: str,
    ):
        """Checks if a table is cached in the local duckdb"""
        destination_table = exp.to_table(table_ref_name)
        self.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {destination_table.db}")
        self.connection.sql(
            f"""
            CREATE TABLE IF NOT EXISTS {destination_table.db}.{destination_table.this.this} AS
            SELECT * FROM {table_actual_name}
        """
        )
