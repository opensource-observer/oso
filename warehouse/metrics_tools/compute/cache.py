import logging
import queue
import typing as t
import uuid
import threading

from pydantic import BaseModel
from sqlglot import exp
from sqlmesh.core.dialect import parse_one
from trino.dbapi import Connection

logger = logging.getLogger(__name__)


class ExportCacheQueueItem(BaseModel):
    table: str


class ExportCacheCompletedQueueItem(BaseModel):
    table: str
    export_table: str


class TrinoCacheExportManager:
    """Manages the export of trino tables to a cache location in GCS that can be
    used easily by duckdb or other compute resources. This is necessary because
    pyiceberg and duckdb's iceberg libraries are quite slow at processing the
    lakehouse data directly."""

    export_queue_thread: threading.Thread
    export_completed_queue_thread: threading.Thread

    @classmethod
    def setup(
        cls,
        db: Connection,
        gcs_bucket: str,
        hive_catalog: str,
        hive_schema: str,
        preloaded_exported_map: t.Optional[t.Dict[str, str]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        cache = cls(
            db,
            gcs_bucket,
            hive_catalog,
            hive_schema,
            preloaded_exported_map=preloaded_exported_map,
            log_override=log_override,
        )
        cache.start()
        return cache

    def __init__(
        self,
        db: Connection,
        gcs_bucket: str,
        hive_catalog: str = "source",
        hive_schema: str = "export",
        preloaded_exported_map: t.Optional[t.Dict[str, str]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.exported_map: t.Dict[str, str] = preloaded_exported_map or {}
        self.gcs_bucket = gcs_bucket
        self.db = db
        self.hive_catalog = hive_catalog
        self.hive_schema = hive_schema
        self.exported_map_lock = threading.Lock()
        self.export_queue: queue.Queue[ExportCacheQueueItem] = queue.Queue()
        self.export_completed_queue: queue.Queue[ExportCacheCompletedQueueItem] = (
            queue.Queue()
        )
        self.stop_signal = threading.Event()
        self.logger = log_override or logger

    def start(self):
        self.stop_signal.clear()
        if not self.export_queue_thread or not self.export_queue_thread.is_alive():
            self.export_queue_thread = threading.Thread(
                target=self._start_export_queue_thread
            )
            self.export_queue_thread.start()

    def _start_export_queue_thread(self):
        """Starts a processing thread to handle the export queue"""
        self.logger.debug("starting export cache manager export queue")
        while True:
            if self.stop_signal.is_set():
                self.logger.info("stopping export cache manager export queue")
                break
            try:
                item = self.export_queue.get(timeout=1)
                self._export_table_for_cache(item.table)
            except queue.Empty:
                continue

    def _start_export_completed_queue_thread(self):
        """Starts a processing thread to handle the export completed queue"""
        self.logger.debug("starting export cache manager export completed queue")
        while True:
            if self.stop_signal.is_set():
                self.logger.info("stopping export cache manager export completed queue")
                break
            try:
                item = self.export_completed_queue.get(timeout=1)
                self.add_export_table_reference(item.table, item.export_table)
            except queue.Empty:
                continue

    def stop(self):
        self.stop_signal.set()

    def run_query(self, query: str):
        cursor = self.db.cursor()
        logger.info(f"EXECUTING: {query}")
        return cursor.execute(query)

    def add_export_table_reference(self, table: str, export_table: str):
        self.add_export_table_references({table: export_table})

    def add_export_table_references(self, table_map: t.Dict[str, str]):
        with self.exported_map_lock:
            self.exported_map.update(table_map)

    def queue_export_table_for_cache(self, table: str):
        self.export_queue.put(ExportCacheQueueItem(table=table))

    def _export_table_for_cache(self, table: str):
        # Using the actual name
        # Export with trino
        with self.exported_map_lock:
            if table in self.exported_map:
                logger.debug(f"CACHE HIT FOR {table}")
                return self.exported_map[table]

        columns: t.List[t.Tuple[str, str]] = []

        col_result = self.run_query(f"SHOW COLUMNS FROM {table}").fetchall()
        for row in col_result:
            column_name = row[0]
            column_type = row[1]
            columns.append((column_name, column_type))

        table_exp = exp.to_table(table)
        logger.info(f"RETREIVED COLUMNS: {columns}")
        export_table_name = f"export_{table_exp.this.this}_{uuid.uuid4().hex}"

        # We use a little bit of a hybrid templating+sqlglot magic to generate
        # the create and insert queries. This saves us having to figure out the
        # exact sqlmesh objects
        base_create_query = f"""
            CREATE table "{self.hive_catalog}"."{self.hive_schema}"."{export_table_name}" (
                placeholder VARCHAR,
            ) WITH (
                format = 'PARQUET',
                external_location = 'gs://{self.gcs_bucket}/trino-export/{export_table_name}/'
            )
        """
        # Parse the create query
        create_query = parse_one(base_create_query)
        # Rewrite the components we need to rewrite
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(
                    this=exp.to_identifier(column_name),
                    kind=parse_one(column_type, into=exp.DataType),
                )
                for column_name, column_type in columns
            ],
        )

        # Execute the create query which will create the export table
        self.run_query(create_query.sql(dialect="trino"))

        base_insert_query = f"""
            INSERT INTO "{self.hive_catalog}"."{self.hive_schema}"."{export_table_name}" (placeholder)
            SELECT placeholder
            FROM {table_exp}
        """

        column_identifiers = [
            exp.to_identifier(column_name) for column_name, _ in columns
        ]

        insert_query = parse_one(base_insert_query)
        insert_query.this.set(
            "expressions",
            column_identifiers,
        )
        select = t.cast(exp.Select, insert_query.expression)
        select.set("expressions", column_identifiers)

        self.run_query(insert_query.sql(dialect="trino"))

        with self.exported_map_lock:
            self.exported_map[table] = export_table_name
            return self.exported_map[table]
