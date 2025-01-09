import logging
import os
import typing as t
import uuid
from datetime import datetime
from urllib.parse import urlparse

from aiotrino.dbapi import Connection
from google.cloud import storage
from metrics_tools.compute.types import (
    ColumnsDefinition,
    ExportReference,
    ExportType,
    TableReference,
)
from metrics_tools.transfer.base import Exporter
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


class TrinoExporter(Exporter):
    def __init__(
        self,
        hive_catalog: str,
        hive_schema: str,
        gcs_bucket: str,
        gcs_client: storage.Client,
        connection: Connection,
        export_base_path: str = "trino-export",
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.logger = log_override or logger
        self.hive_catalog = hive_catalog
        self.hive_schema = hive_schema
        self.gcs_bucket = gcs_bucket
        self.connection = connection
        self.export_base_path = export_base_path
        self.gcs_client = gcs_client

    async def run_query(self, query: str):
        cursor = await self.connection.cursor()
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

    async def export_table(
        self,
        table: TableReference,
        supported_types: t.Set[ExportType],
        export_time: t.Optional[datetime] = None,
    ) -> ExportReference:
        # Trino only supports GCS exports
        if ExportType.GCS not in supported_types:
            raise ValueError("Trino only supports GCS exports")

        columns: t.List[t.Tuple[str, str]] = []
        export_time = export_time or datetime.now()

        col_result = await self.run_query(f"SHOW COLUMNS FROM {table.fqn}")

        for row in col_result:
            column_name = row[0]
            column_type = row[1]
            columns.append((column_name, column_type))

        table_exp = exp.to_table(table.fqn)
        self.logger.debug(f"retrieved columns for {table} export: {columns}")
        export_table_name = f"export_{table_exp.this.this}_{uuid.uuid4().hex}"

        # We make cleaning easier by using the export time to allow listing
        # of the export tables
        gcs_path = f"gs://{self.gcs_bucket}/{self.export_base_path}/{export_time.strftime('%Y/%m/%d/%H')}/{export_table_name}/"

        export_table_fqn = (
            f'"{self.hive_catalog}"."{self.hive_schema}"."{export_table_name}"'
        )

        # We use a little bit of a hybrid templating+sqlglot magic to generate
        # the create and insert queries. This saves us having to figure out the
        # exact sqlglot objects
        base_create_query = f"""
            CREATE table {export_table_fqn} (
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
            INSERT INTO {export_table_fqn} (placeholder)
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

        # Drop the temporary table. The data won't be deleted but the reference
        # in the hive metastore will be
        await self.run_query(f"DROP TABLE IF EXISTS {export_table_fqn}")

        return ExportReference(
            table=TableReference(table_name=table.table_name),
            type=ExportType.GCS,
            payload={"gcs_path": gcs_path},
            columns=ColumnsDefinition(columns=columns, dialect="trino"),
        )

    def export_path(self, export_time: datetime, export_table_name: str):
        return f"gs://{self.gcs_bucket}/{self.export_base_path}/{export_time.strftime('%Y/%m/%d/%H')}/{export_table_name}/"

    async def cleanup_ref(self, export_reference: ExportReference):
        # Delete the table from the hive catalog if it's there
        gcs_path = export_reference.payload["gcs_path"]
        parsed_gcs_path = urlparse(gcs_path)
        export_table_name = os.path.basename(parsed_gcs_path.path.strip("/"))

        drop_query = f"DROP TABLE IF EXISTS {self.hive_catalog}.{self.hive_schema}.{export_table_name}"
        logger.debug(f"Running drop query: {drop_query}")
        await self.run_query(drop_query)

        # Delete everything in the gcs path
        bucket = self.gcs_client.get_bucket(self.gcs_bucket)
        blobs = bucket.list_blobs(prefix=parsed_gcs_path.path.strip("/"))

        for blob in blobs:
            logger.debug(f"Deleting blob: {blob.name}")
            blob.delete(if_generation_match=blob.generation)

    async def cleanup_expired(self, expiration: datetime, dry_run: bool = False):
        # Search for any tables that are older than the expiration date
        bucket = self.gcs_client.get_bucket(self.gcs_bucket)
        blobs = bucket.list_blobs(prefix=self.export_base_path)

        # Track dropped tables so we don't try to drop them again unnecessarily
        dropped_tables = set()

        # We use the gcs path to determine the export time and delete any files
        # that are older than the expiration date.
        for blob in blobs:
            name = t.cast(str, blob.name)
            export_rel_path = os.path.relpath(name, self.export_base_path)
            path_parts = export_rel_path.split("/")

            if len(path_parts) < 6:
                continue

            export_time = datetime.strptime("/".join(path_parts[0:4]), "%Y/%m/%d/%H")

            if export_time < expiration:
                table_name = path_parts[4]
                if table_name not in dropped_tables:
                    drop_query = f"DROP TABLE IF EXISTS {self.hive_catalog}.{self.hive_schema}.{table_name}"
                    if not dry_run:
                        logger.debug(f"Running drop query: {drop_query}")
                        await self.run_query(drop_query)
                    else:
                        logger.debug(f"Would have run: {drop_query}")
                    dropped_tables.add(table_name)

                if not dry_run:
                    logger.debug(f"Deleting blob: {blob.name}")
                    blob.delete(if_generation_match=blob.generation)
                else:
                    logger.debug(f"Would have deleted: {blob.name}")
