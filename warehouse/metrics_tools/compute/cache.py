import abc
import asyncio
import copy
import logging
import queue
import typing as t
import uuid

from pydantic import BaseModel
from sqlglot import exp
from sqlmesh.core.dialect import parse_one
from aiotrino.dbapi import Connection
from pyee.asyncio import AsyncIOEventEmitter

from .types import ExportReference, ExportType

logger = logging.getLogger(__name__)


class ExportCacheCompletedQueueItem(BaseModel):
    table: str
    export_table: str


class ExportCacheQueueItem(BaseModel):
    table: str


class DBExportAdapter(abc.ABC):
    async def export_table(self, table: str) -> ExportReference:
        raise NotImplementedError()

    async def clean_export_table(self, table: str):
        raise NotImplementedError()


class FakeExportAdapter(DBExportAdapter):
    def __init__(self, log_override: t.Optional[logging.Logger] = None):
        self.logger = log_override or logger

    async def export_table(self, table: str) -> ExportReference:
        self.logger.info(f"fake exporting table: {table}")
        return ExportReference(
            table=table, type=ExportType.GCS, payload={"gcs_path": "fake_path:{table}"}
        )

    async def clean_export_table(self, table: str):
        pass


class TrinoExportAdapter(DBExportAdapter):
    def __init__(
        self,
        db: Connection,
        gcs_bucket: str,
        hive_catalog: str,
        hive_schema: str,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.db = db
        self.gcs_bucket = gcs_bucket
        self.hive_catalog = hive_catalog
        self.hive_schema = hive_schema
        self.logger = log_override or logger

    async def export_table(self, table: str) -> ExportReference:
        columns: t.List[t.Tuple[str, str]] = []

        col_result = await self.run_query(f"SHOW COLUMNS FROM {table}")

        for row in col_result:
            column_name = row[0]
            column_type = row[1]
            columns.append((column_name, column_type))

        table_exp = exp.to_table(table)
        self.logger.debug(f"retrieved columns for {table} export: {columns}")
        export_table_name = f"export_{table_exp.this.this}_{uuid.uuid4().hex}"

        gcs_path = f"gs://{self.gcs_bucket}/trino-export/{export_table_name}/"

        # We use a little bit of a hybrid templating+sqlglot magic to generate
        # the create and insert queries. This saves us having to figure out the
        # exact sqlglot objects
        base_create_query = f"""
            CREATE table "{self.hive_catalog}"."{self.hive_schema}"."{export_table_name}" (
                placeholder VARCHAR,
            ) WITH (
                format = 'PARQUET',
                external_location = '{gcs_path}'
            )
        """

        # Parse the create query
        create_query = parse_one(base_create_query)
        # Rewrite the column definitions we need to rewrite
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
        await self.run_query(create_query.sql(dialect="trino"))

        # Again using a hybrid templating+sqlglot magic to generate the insert
        # for the export table
        base_insert_query = f"""
            INSERT INTO "{self.hive_catalog}"."{self.hive_schema}"."{export_table_name}" (placeholder)
            SELECT placeholder
            FROM {table_exp}
        """

        column_identifiers = [
            exp.to_identifier(column_name) for column_name, _ in columns
        ]

        # Rewrite the column identifiers in the insert into statement
        insert_query = parse_one(base_insert_query)
        insert_query.this.set(
            "expressions",
            column_identifiers,
        )

        # Rewrite the column identifiers in the select statement
        select = t.cast(exp.Select, insert_query.expression)
        select.set("expressions", column_identifiers)

        # Execute the insert query which will populate the export table
        await self.run_query(insert_query.sql(dialect="trino"))

        return ExportReference(
            table=table, type=ExportType.GCS, payload={"gcs_path": gcs_path}
        )

    async def run_query(self, query: str):
        cursor = await self.db.cursor()
        self.logger.info(f"EXECUTING: {query}")
        await cursor.execute(query)
        return await cursor.fetchall()

    async def clean_export_table(self, table: str):
        pass


def setup_trino_cache_export_manager(
    db: Connection,
    gcs_bucket: str,
    hive_catalog: str,
    hive_schema: str,
    preloaded_exported_map: t.Optional[t.Dict[str, ExportReference]] = None,
    log_override: t.Optional[logging.Logger] = None,
):
    adapter = TrinoExportAdapter(
        db, gcs_bucket, hive_catalog, hive_schema, log_override=log_override
    )
    return CacheExportManager.setup(
        export_adapter=adapter,
        preloaded_exported_map=preloaded_exported_map,
        log_override=log_override,
    )


def setup_fake_cache_export_manager(
    preloaded_exported_map: t.Optional[t.Dict[str, ExportReference]] = None,
    log_override: t.Optional[logging.Logger] = None,
):
    adapter = FakeExportAdapter()
    return CacheExportManager.setup(
        export_adapter=adapter,
        preloaded_exported_map=preloaded_exported_map,
        log_override=log_override,
    )


class CacheExportManager:
    """Manages the export of tables to a cache location. For now this only
    supports GCS and can be used easily by duckdb or other compute resources.
    This is necessary because pyiceberg and duckdb's iceberg libraries are quite
    slow at processing the lakehouse data directly. In the future we'd simply
    want to use iceberg directly but for now this is a necessary workaround.

    This class requires a database export adapter. The adapter is called to
    trigger the database export. Once the export is completed any consumers of
    this export manager can listen for the `exported_table` event to know when
    the export is complete.
    """

    export_queue_task: asyncio.Task
    export_queue: asyncio.Queue[ExportCacheQueueItem]
    event_emitter: AsyncIOEventEmitter

    @classmethod
    async def setup(
        cls,
        export_adapter: DBExportAdapter,
        preloaded_exported_map: t.Optional[t.Dict[str, ExportReference]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        cache = cls(
            export_adapter,
            preloaded_exported_map=preloaded_exported_map,
            log_override=log_override,
        )
        await cache.start()
        return cache

    def __init__(
        self,
        export_adapter: DBExportAdapter,
        preloaded_exported_map: t.Optional[t.Dict[str, ExportReference]] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.exported_map: t.Dict[str, ExportReference] = preloaded_exported_map or {}
        self.export_adapter = export_adapter
        self.exported_map_lock = asyncio.Lock()
        self.export_queue: asyncio.Queue[ExportCacheQueueItem] = asyncio.Queue()
        self.export_completed_queue: queue.Queue[ExportCacheCompletedQueueItem] = (
            queue.Queue()
        )
        self.stop_signal = asyncio.Event()
        self.logger = log_override or logger
        self.event_emitter = AsyncIOEventEmitter()

    async def start(self):
        self.export_queue_task = asyncio.create_task(self.export_queue_loop())

    async def stop(self):
        self.stop_signal.set()
        await self.export_queue_task

    async def export_queue_loop(self):
        in_progress: t.Set[str] = set()

        async def export_table(table: str):
            try:
                return await self._export_table_for_cache(table)
            except Exception as e:
                self.logger.error(f"Error exporting table {table}: {e}")
                in_progress.remove(table)

        while not self.stop_signal.is_set():
            try:
                item = await asyncio.wait_for(self.export_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            if item.table in in_progress:
                # The table is already being exported. Skip this in the queue
                continue
            in_progress.add(item.table)
            export_reference = await export_table(item.table)
            self.event_emitter.emit(
                "exported_table", table=item.table, export_reference=export_reference
            )
            self.export_queue.task_done()

    async def add_export_table_reference(
        self, table: str, export_reference: ExportReference
    ):
        await self.add_export_table_references({table: export_reference})

    async def add_export_table_references(
        self, table_map: t.Dict[str, ExportReference]
    ):
        async with self.exported_map_lock:
            self.exported_map.update(table_map)

    async def inspect_export_table_references(self):
        async with self.exported_map_lock:
            return copy.deepcopy(self.exported_map)

    async def get_export_table_reference(self, table: str):
        async with self.exported_map_lock:
            reference = self.exported_map.get(table)
            if not reference:
                return None
            return copy.deepcopy(reference)

    async def _export_table_for_cache(self, table: str):
        """Triggers an export of a table to a cache location in GCS. This does
        this by using the Hive catalog in trino to create a new table with the
        same schema as the original table, but with a different name. This new
        table is then used as the cache location for the original table."""

        export_reference = await self.export_adapter.export_table(table)
        self.logger.info(f"exported table: {table} -> {export_reference}")
        return export_reference

    async def resolve_export_references(self, tables: t.List[str]):
        """Resolves any required export table references or queues up a list of
        tables to be exported to a cache location. Once ready, the map of tables
        is resolved."""
        future: asyncio.Future[t.Dict[str, ExportReference]] = (
            asyncio.get_event_loop().create_future()
        )

        tables_to_export = set(tables)
        registration = None
        export_map: t.Dict[str, ExportReference] = {}

        # Ensure we are only comparing unique tables
        for table in set(tables):
            reference = await self.get_export_table_reference(table)
            if reference is not None:
                export_map[table] = reference
                tables_to_export.remove(table)
        if len(tables_to_export) == 0:
            return export_map

        self.logger.info(f"unknown tables to export: {tables_to_export}")

        async def handle_exported_table(
            *, table: str, export_reference: ExportReference
        ):
            self.logger.info(f"exported table ready: {table} -> {export_reference}")
            if table in tables_to_export:
                tables_to_export.remove(table)
                export_map[table] = export_reference
                await self.add_export_table_reference(table, export_reference)
            if len(tables_to_export) == 0:
                future.set_result(export_map)
                if registration:
                    self.event_emitter.remove_listener("exported_table", registration)

        registration = self.event_emitter.add_listener(
            "exported_table", handle_exported_table
        )
        for table in tables_to_export:
            self.export_queue.put_nowait(ExportCacheQueueItem(table=table))
        return await future
