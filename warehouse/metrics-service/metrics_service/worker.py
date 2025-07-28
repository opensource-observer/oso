# The worker initialization
import logging
import os
import time
import typing as t
import uuid
from contextlib import contextmanager
from threading import Lock

import duckdb
import gcsfs
import polars as pl
from dask.distributed import Worker, WorkerPlugin, get_worker
from google.cloud import storage
from metrics_service.types import ExportReference, ExportType
from oso_core.logging import setup_module_logging
from sqlglot import exp

logger = logging.getLogger(__name__)

mutex = Lock()


class MetricsWorkerPlugin(WorkerPlugin):
    logger: logging.Logger

    def setup(self, worker: Worker):
        setup_module_logging("metrics_tools")
        logger.info("setting up metrics worker plugin")

    def teardown(self, worker: Worker):
        logger.info("tearing down metrics worker plugin")

    def handle_query(
        self,
        job_id: str,
        task_id: str,
        result_path: str,
        queries: t.List[str],
        dependencies: t.Dict[str, ExportReference],
    ) -> t.Any:
        """Execute a query on the worker"""
        raise NotImplementedError()


class DummyMetricsWorkerPlugin(MetricsWorkerPlugin):
    def handle_query(
        self,
        job_id: str,
        task_id: str,
        result_path: str,
        queries: t.List[str],
        dependencies: t.Dict[str, ExportReference],
    ) -> t.Any:
        logger.info(f"job[{job_id}][{task_id}]: dummy executing query {queries}")
        logger.info(f"job[{job_id}][{task_id}]: deps received: {dependencies}")
        logger.info(f"job[{job_id}][{task_id}]: result_path: {result_path}")
        time.sleep(1)
        return task_id


class DuckDBMetricsWorkerPlugin(MetricsWorkerPlugin):
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
        self._fs = None
        self._cache_status: t.Dict[str, bool] = {}
        self._catalog = None
        self._mode = "duckdb"
        self._uuid = uuid.uuid4().hex
        self.logger = logger

    def setup(self, worker: Worker):
        setup_module_logging("metrics_tools")
        logger.info("setting up metrics worker plugin")

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
        self._fs = gcsfs.GCSFileSystem()

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
        export_reference: ExportReference,
    ):
        """Checks if a table is cached in the local duckdb"""
        logger.info(
            f"[{self._uuid}] got a cache request for {table_ref_name}:{export_reference.table.table_name}"
        )
        assert export_reference.type == ExportType.GCS, "Only GCS exports are supported"
        assert export_reference.payload.get("gcs_path") is not None, (
            "A gcs_path is required"
        )

        if self._cache_status.get(table_ref_name):
            return
        with mutex:
            if self._cache_status.get(table_ref_name):
                return
            destination_table = exp.to_table(table_ref_name)

            gcs_path = export_reference.payload["gcs_path"]

            self.load_using_gcs_parquet(table_ref_name, gcs_path, destination_table)

            self._cache_status[table_ref_name] = True

    def load_using_gcs_parquet(
        self,
        table_ref_name: str,
        gcs_path: str,
        destination_table: exp.Table,
    ):
        self.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {destination_table.db}")
        logger.info(f"CACHING TABLE {table_ref_name} WITH PARQUET")

        path_to_load = os.path.join(gcs_path, "*")

        cache_sql = f"""
            CREATE TABLE IF NOT EXISTS "{destination_table.db}"."{destination_table.this.this}" AS
            SELECT * FROM read_parquet('{path_to_load}')
        """
        logger.debug(f"Executing SQL: {cache_sql}")
        self.connection.sql(cache_sql)
        logger.info(f"LOADING EXPORTED TABLE {table_ref_name} COMPLETED")

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

    def upload_to_gcs_bucket(self, blob_path: str, file: t.IO):
        with self.gcs_client() as client:
            bucket = client.bucket(self._gcs_bucket)
            blob = bucket.blob(blob_path)
            blob.upload_from_file(file)

    @property
    def fs(self):
        assert self._fs is not None, "GCSFS not initialized"
        return self._fs

    def handle_query(
        self,
        job_id: str,
        task_id: str,
        result_path: str,
        queries: t.List[str],
        dependencies: t.Dict[str, ExportReference],
    ) -> t.Any:
        """Execute a duckdb load on a worker.

        This executes the query with duckdb and writes the results to a gcs
        path. We need to use polars or pyarrow here because the pandas parquet
        writer doesn't write the correct datatypes for trino.
        """

        for ref, actual in dependencies.items():
            self.logger.info(
                f"job[{job_id}][{task_id}] Loading cache for {ref}:{actual}"
            )
            self.get_for_cache(ref, actual)
        conn = self.connection
        results: t.List[pl.DataFrame] = []
        for query in queries:
            self.logger.info(f"job[{job_id}][{task_id}]: Executing query {query}")
            result = conn.execute(query).pl()
            results.append(result)
        # Concatenate the results
        self.logger.info(f"job[{job_id}][{task_id}]: Concatenating results")
        combined_results = pl.concat(results)

        # Export the results to a parquet file in memory
        self.logger.info(
            f"job[{job_id}][{task_id}]: Uploading to gcs {result_path} with polars"
        )
        with self.fs.open(f"{self._gcs_bucket}/{result_path}", "wb") as f:
            combined_results.write_parquet(f)  # type: ignore
        self.logger.info(f"job[{job_id}][{task_id}]: Upload completed")
        return task_id


def execute_duckdb_load(
    job_id: str,
    task_id: str,
    result_path: str,
    queries: t.List[str],
    dependencies: t.Dict[str, ExportReference],
):
    """Execute a duckdb load on a worker.

    This executes the query with duckdb and writes the results to a gcs path.
    """
    worker = get_worker()

    # The metrics plugin keeps a record of the cached tables on the worker.
    plugin = t.cast(MetricsWorkerPlugin, worker.plugins["metrics"])
    plugin.handle_query(job_id, task_id, result_path, queries, dependencies)

    return task_id


def bad_execute(*args, **kwargs):
    """Intentionally throws an exception

    Used for testing error handling
    """
    worker = get_worker()

    # The metrics plugin keeps a record of the cached tables on the worker.
    plugin = t.cast(MetricsWorkerPlugin, worker.plugins["metrics"])
    plugin.logger.info("Intentionally throwing an exception")

    raise ValueError("Intentionally throwing an exception")


def noop_execute(job_id: str, task_id: str, *args, **kwargs):
    """Does nothing

    Used for testing
    """
    worker = get_worker()

    # The metrics plugin keeps a record of the cached tables on the worker.
    plugin = t.cast(MetricsWorkerPlugin, worker.plugins["metrics"])
    plugin.logger.info("Doing nothing")
    return task_id
