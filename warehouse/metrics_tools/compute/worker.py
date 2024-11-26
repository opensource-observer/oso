# The worker initialization
import abc
import logging
import os
import sys
import typing as t
import uuid
from contextlib import contextmanager
from threading import Lock

import duckdb
import polars as pl
from dask.distributed import Worker, WorkerPlugin, get_worker
from google.cloud import storage
from metrics_tools.utils.logging import add_metrics_tools_to_existing_logger
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table as IcebergTable
from sqlglot import exp

logger = logging.getLogger(__name__)

mutex = Lock()


class MetricsWorkerPlugin(WorkerPlugin):
    def __init__(
        self,
        gcs_bucket: str,
        gcs_key_id: str,
        gcs_secret: str,
        duckdb_path: str,
    ):
        self._gcs_bucket = gcs_bucket
        self._gcs_key_id = gcs_key_id
        self._gcs_secret = gcs_secret
        self._duckdb_path = duckdb_path
        self._conn = None
        self._cache_status: t.Dict[str, bool] = {}
        self._catalog = None
        self._mode = "duckdb"
        self._uuid = uuid.uuid4().hex

    def setup(self, worker: Worker):
        add_metrics_tools_to_existing_logger("distributed")
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

        self._conn = duckdb.connect(self._duckdb_path)

        # Connect to gcs
        sql = f"""
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
        return self._conn.cursor()

    def get_for_cache(
        self,
        table_ref_name: str,
        table_actual_name: str,
    ):
        """Checks if a table is cached in the local duckdb"""
        logger.info(
            f"[{self._uuid}] got a cache request for {table_ref_name}:{table_actual_name}"
        )
        if self._cache_status.get(table_ref_name):
            return
        with mutex:
            if self._cache_status.get(table_ref_name):
                return
            destination_table = exp.to_table(table_ref_name)

            # if self._mode == "duckdb":
            #     self.load_using_duckdb(
            #         table_ref_name, table_actual_name, destination_table, table
            #     )
            # else:
            #     self.load_using_pyiceberg(
            #         table_ref_name, table_actual_name, destination_table, table
            #     )
            self.load_using_gcs_parquet(
                table_ref_name, table_actual_name, destination_table
            )

            self._cache_status[table_ref_name] = True

    def load_using_duckdb(
        self,
        table_ref_name: str,
        table_actual_name: str,
        destination_table: exp.Table,
    ):
        source_table = exp.to_table(table_actual_name)
        assert self._catalog is not None
        table = self._catalog.load_table((source_table.db, source_table.this.this))

        self.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {destination_table.db}")
        caching_sql = f"""
            CREATE TABLE IF NOT EXISTS {destination_table.db}.{destination_table.this.this} AS
            SELECT * FROM iceberg_scan('{table.metadata_location}')
        """
        logger.info(f"CACHING TABLE {table_ref_name} WITH SQL: {caching_sql}")
        self.connection.sql(caching_sql)
        logger.info(f"CACHING TABLE {table_ref_name} COMPLETED")

    def load_using_pyiceberg(
        self,
        table_ref_name: str,
        table_actual_name: str,
        destination_table: exp.Table,
        table: IcebergTable,
    ):
        source_table = exp.to_table(table_actual_name)
        assert self._catalog is not None
        table = self._catalog.load_table((source_table.db, source_table.this.this))
        batch_reader = table.scan().to_arrow_batch_reader()  # noqa: F841
        self.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {destination_table.db}")
        logger.info(f"CACHING TABLE {table_ref_name} WITH ICEBERG")
        self.connection.sql(
            f"""
            CREATE TABLE IF NOT EXISTS {destination_table.db}.{destination_table.this.this} AS
            SELECT * FROM batch_reader
        """
        )
        logger.info(f"CACHING TABLE {table_ref_name} COMPLETED")

    def load_using_gcs_parquet(
        self,
        table_ref_name: str,
        table_actual_name: str,
        destination_table: exp.Table,
    ):
        self.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {destination_table.db}")
        logger.info(f"CACHING TABLE {table_ref_name} WITH PARQUET")
        self.connection.sql(
            f"""
            CREATE TABLE IF NOT EXISTS {destination_table.db}.{destination_table.this.this} AS
            SELECT * FROM read_parquet('gs://{self._gcs_bucket}/trino-export/{table_actual_name}/*')
        """
        )
        logger.info(f"CACHING TABLE {table_ref_name} COMPLETED")

    @contextmanager
    def gcs_client(self):
        client = storage.Client()
        try:
            yield client
        finally:
            client.close()

    @property
    def bucket(self):
        return self._gcs_bucket

    def bucket_path(self, *joins: str):
        return os.path.join(f"gs://{self.bucket}", *joins)


def execute_duckdb_load(
    id: int, gcs_path: str, queries: t.List[str], dependencies: t.Dict[str, str]
):
    logger.debug("Starting duckdb load")
    worker = get_worker()
    plugin = t.cast(MetricsWorkerPlugin, worker.plugins["metrics"])
    for ref, actual in dependencies.items():
        logger.debug(f"Loading cache for {ref}:{actual}")
        plugin.get_for_cache(ref, actual)
    conn = plugin.connection
    results: t.List[pl.DataFrame] = []
    for query in queries:
        result = conn.execute(query).pl()
        results.append(result)

    pl.concat(results)

    # return DuckdbLoadedItem(
    #     id=id,
    #     df=pd.concat(results, ignore_index=True, sort=False),
    # )
