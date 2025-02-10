import abc
import asyncio
import copy
import logging
import queue
import typing as t
import uuid
from datetime import datetime

from aiotrino.dbapi import Connection
from pydantic import BaseModel
from pyee.asyncio import AsyncIOEventEmitter
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

from .types import ColumnsDefinition, ExportReference, ExportType, TableReference

logger = logging.getLogger(__name__)


class ExportCacheCompletedQueueItem(BaseModel):
    table: str
    export_table: str


class ExportCacheQueueItem(BaseModel):
    execution_time: datetime
    table: str


class ExportError(Exception):
    def __init__(self, table: str, error: Exception):
        self.table = table
        self.error = error


class DBExportAdapter(abc.ABC):
    async def export_table(
        self, table: str, execution_time: datetime
    ) -> ExportReference:
        raise NotImplementedError()

    async def clean_export_table(self, table: str):
        raise NotImplementedError()


class FakeExportAdapter(DBExportAdapter):
    def __init__(self, log_override: t.Optional[logging.Logger] = None):
        self.logger = log_override or logger

    async def export_table(
        self, table: str, execution_time: datetime
    ) -> ExportReference:
        self.logger.info(f"fake exporting table: {table}")
        return ExportReference(
            table=TableReference(table_name=table),
            type=ExportType.GCS,
            payload={"gcs_path": "fake_path:{table}"},
            columns=ColumnsDefinition(columns=[]),
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

    async def export_table(
        self, table: str, execution_time: datetime
    ) -> ExportReference:
        columns: t.List[t.Tuple[str, str]] = []

        col_result = await self.run_query(f"SHOW COLUMNS FROM {table}")

        for row in col_result:
            column_name = row[0]
            column_type = row[1]
            columns.append((column_name, column_type))

        table_exp = exp.to_table(table)
        self.logger.debug(f"retrieved columns for {table} export: {columns}")
        export_table_name = f"export_{table_exp.this.this}_{uuid.uuid4().hex}"

        # We make cleaning easier by using the execution time to allow listing
        # of the export tables
        gcs_path = f"gs://{self.gcs_bucket}/trino-export/{execution_time.strftime('%Y/%m/%d/%H')}/{export_table_name}/"

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

        # Trino's hive connector has some issues with certain column types so we
        # will forcibly cast those columns to values that will work
        processed_columns: t.List[
            t.Tuple[exp.Identifier, exp.ColumnDef, exp.Expression]
        ] = [
            self.process_columns(column_name, parse_one(column_type, into=exp.DataType))
            for column_name, column_type in columns
        ]

        # Parse the create query
        create_query = parse_one(base_create_query)
        # Rewrite the column definitions we need to rewrite.

        create_query.this.set("expressions", [row[1] for row in processed_columns])

        # Execute the create query which will create the export table
        await self.run_query(create_query.sql(dialect="trino"))

        # Again using a hybrid templating+sqlglot magic to generate the insert
        # for the export table
        base_insert_query = f"""
            INSERT INTO "{self.hive_catalog}"."{self.hive_schema}"."{export_table_name}" (placeholder)
            SELECT placeholder
            FROM {table_exp}
        """

        column_identifiers = [row[0] for row in processed_columns]
        column_selects = [row[2] for row in processed_columns]

        # Rewrite the column identifiers in the insert into statement
        insert_query = parse_one(base_insert_query)
        insert_query.this.set(
            "expressions",
            column_identifiers,
        )

        # Rewrite the column identifiers in the select statement
        select = t.cast(exp.Select, insert_query.expression)
        select.set("expressions", column_selects)

        # Execute the insert query which will populate the export table
        await self.run_query(insert_query.sql(dialect="trino"))

        return ExportReference(
            table=TableReference(table_name=table),
            type=ExportType.GCS,
            payload={"gcs_path": gcs_path},
            columns=ColumnsDefinition(columns=columns, dialect="trino"),
        )

    async def run_query(self, query: str):
        cursor = await self.db.cursor()
        self.logger.info(f"Executing SQL: {query}")
        await cursor.execute(query)
        return await cursor.fetchall()

    def process_columns(
        self, column_name: str, column_type: exp.Expression
    ) -> t.Tuple[exp.Identifier, exp.ColumnDef, exp.Expression]:
        assert isinstance(
            column_type, exp.DataType
        ), "column_type must parse into DataType"

        self.logger.debug(
            f"creating column def for column_name: {column_name} column_type: {column_type}"
        )
        column_select = exp.to_identifier(column_name)
        column_identifier = exp.to_identifier(column_name)

        if column_type.this == exp.DataType.Type.TIMESTAMPTZ:
            # We need to cast the timestamptz to a timestamp without time zone that is
            # compatible with the hive connector
            column_type = exp.DataType(this=exp.DataType.Type.TIMESTAMP, nested=False)
            column_select = exp.Cast(
                this=exp.Anonymous(
                    this="at_timezone",
                    expressions=[
                        exp.to_identifier(column_name),
                        exp.Literal(this="UTC", is_string=True),
                    ],
                ),
                to=column_type,
            )
        elif column_type.this == exp.DataType.Type.TIMESTAMP:
            column_type = exp.DataType(this=exp.DataType.Type.TIMESTAMP, nested=False)
            column_select = exp.Cast(
                this=exp.to_identifier(column_name),
                to=column_type,
            )
        return (
            column_identifier,
            exp.ColumnDef(this=column_identifier, kind=column_type),
            column_select,
        )

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
        errors: t.Dict[str, t.List[Exception]] = {}

        async def export_table(id: str, table: str, execution_time: datetime):
            export_table_key = self.export_table_key(table, execution_time)
            try:
                export_reference = await self._export_table_for_cache(
                    table, execution_time
                )
                self.event_emitter.emit(
                    "exported_table",
                    table=item.table,
                    execution_time=item.execution_time,
                    export_table_key=export_table_key,
                    export_reference=export_reference,
                )
                self.export_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error exporting table {table}: {e}")

                # Save the error for later
                table_errors = errors.get(export_table_key, [])
                table_errors.append(e)
                errors[export_table_key] = table_errors

                in_progress.remove(export_table_key)
                self.event_emitter.emit(
                    "exported_table",
                    table=table,
                    execution_time=item.execution_time,
                    export_table_key=export_table_key,
                    error=e,
                )
                self.logger.debug("emitted error event and waiting for next export")
                self.export_queue.task_done()
            tasks.pop(id)

        tasks: t.Dict[str, asyncio.Task] = {}
        count = 0
        self.logger.info("export queue loop started")
        while not self.stop_signal.is_set():
            count += 1
            try:
                item = await asyncio.wait_for(self.export_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                if count % 60 == 0:
                    self.logger.debug("export queue loop is still running")
                continue
            except asyncio.CancelledError:
                continue
            except RuntimeError:
                break
            self.logger.debug(f"export queue item received: {item}")
            export_table_key = self.export_table_key(item.table, item.execution_time)
            if export_table_key in in_progress:
                # The table is already being exported. Skip this in the queue
                continue
            if export_table_key in errors:
                # The table has already errored. Skip this in the queue
                continue

            in_progress.add(export_table_key)

            export_task_id = uuid.uuid4().hex
            tasks[export_task_id] = asyncio.create_task(
                export_table(export_task_id, item.table, item.execution_time)
            )

        tasks_list = list(tasks.values())
        self.logger.info(f"waiting for {len(tasks_list)} tasks to complete")

        await asyncio.gather(*tasks_list)

    async def add_export_table_reference(
        self, table: str, execution_time: datetime, export_reference: ExportReference
    ):
        export_table_key = self.export_table_key(table, execution_time)
        await self.add_export_table_references({export_table_key: export_reference})

    async def add_export_table_references(
        self, table_map: t.Dict[str, ExportReference]
    ):
        async with self.exported_map_lock:
            self.exported_map.update(table_map)

    async def inspect_export_table_references(self):
        async with self.exported_map_lock:
            return copy.deepcopy(self.exported_map)

    def export_table_key(self, table: str, execution_time: datetime):
        return f"{table}::{execution_time.isoformat()}"

    async def get_export_table_reference(self, table: str, execution_time: datetime):
        export_table_key = self.export_table_key(table, execution_time)

        async with self.exported_map_lock:
            reference = self.exported_map.get(export_table_key)
            if not reference:
                return None
            return copy.deepcopy(reference)

    async def _export_table_for_cache(self, table: str, execution_time: datetime):
        """Triggers an export of a table to a cache location in GCS. This does
        this by using the Hive catalog in trino to create a new table with the
        same schema as the original table, but with a different name. This new
        table is then used as the cache location for the original table."""

        export_reference = await self.export_adapter.export_table(table, execution_time)
        self.logger.info(f"exported table: {table} -> {export_reference}")
        return export_reference

    async def resolve_export_references(
        self, tables: t.List[str], execution_time: datetime
    ):
        """Resolves any required export table references or queues up a list of
        tables to be exported to a cache location. Once ready, the map of tables
        is resolved."""
        future: asyncio.Future[t.Dict[str, ExportReference]] = (
            asyncio.get_event_loop().create_future()
        )

        # The tables to export should be unique combinations of the table name
        # and execution time. This ensures that multiple runs don't use stale
        # data accidentally.
        tables_to_export = set(tables)
        registration = None
        export_map: t.Dict[str, ExportReference] = {}

        # Ensure we are only comparing unique tables
        for table in set(tables):
            reference = await self.get_export_table_reference(table, execution_time)
            if reference is not None:
                export_map[table] = reference
                tables_to_export.remove(table)
        if len(tables_to_export) == 0:
            return export_map
        pending_export_table_keys = set(
            [self.export_table_key(table, execution_time) for table in tables_to_export]
        )

        self.logger.info(f"unknown tables to export: {tables_to_export}")

        async def handle_exported_table(
            *,
            table: str,
            execution_time: datetime,
            export_table_key: str,
            export_reference: t.Optional[ExportReference] = None,
            error: t.Optional[Exception] = None,
        ):
            if not export_reference and not error:
                self.logger.error("export_reference or error must be provided")
                raise RuntimeError("export_reference or error must be provided")

            # If there was an error send it back to the listener
            self.logger.info(
                f"exported table update received: {table} :: {execution_time}"
            )
            self.logger.debug(
                f"Checking pending export table keys: {pending_export_table_keys}"
            )
            self.logger.debug(f"Checking export table key: {export_table_key}")
            # Check if we were waiting for this table
            if export_table_key in pending_export_table_keys:
                self.logger.debug("found pending export table key")
                # If there's no export reference then we must have an error
                if not export_reference:
                    assert error is not None
                    future.set_exception(error)
                    return
                pending_export_table_keys.remove(export_table_key)
                export_map[table] = export_reference
                await self.add_export_table_reference(
                    table, execution_time, export_reference
                )
            # Stop listening if we have all the tables
            if len(pending_export_table_keys) == 0:
                self.logger.debug("all tables exported")
                future.set_result(export_map)
                if registration:
                    self.event_emitter.remove_listener("exported_table", registration)

        registration = self.event_emitter.add_listener(
            "exported_table", handle_exported_table
        )
        for table in tables_to_export:
            self.logger.info(f"queueing table for export: {table}")
            self.export_queue.put_nowait(
                ExportCacheQueueItem(table=table, execution_time=execution_time)
            )
        return await future
