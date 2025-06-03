"""
For now the results for the metrics calculations are stored in a gcs bucket. We
can list all of those results and deterministically resolve those to trino
tables as well.
"""

import abc
import logging
import os
import typing as t
from datetime import datetime

import numpy as np
import pandas as pd
from aiotrino.dbapi import Connection
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

from .types import ExportReference, ExportType, TableReference

logger = logging.getLogger(__name__)


class DBImportAdapter(abc.ABC):
    async def import_reference(
        self, source_ref: ExportReference, dest_ref: ExportReference
    ):
        raise NotImplementedError()

    async def translate_reference(self, reference: ExportReference) -> ExportReference:
        raise NotImplementedError()

    async def clean(self, table: str):
        raise NotImplementedError()

    async def clean_expired(self, expiration: datetime):
        """Used to clean old imported tables that might not be needed. This is
        not required to do anything all import adapters"""
        return


class DummyImportAdapter(DBImportAdapter):
    """A dummy import adapter that does nothing. This is useful for testing
    basic operations of the service"""

    async def import_reference(
        self, source_ref: ExportReference, dest_ref: ExportReference
    ):
        return

    async def translate_reference(self, reference: ExportReference) -> ExportReference:
        return reference

    async def clean(self, table: str):
        pass

    async def clean_expired(self, expiration: datetime):
        pass


class FakeLocalImportAdapter(DBImportAdapter):
    """A fake import adapter that writes random data to a temporary directory.
    This allows us to use this with duckdb for testing purposes"""

    def __init__(
        self,
        temp_dir: str,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.temp_dir = temp_dir
        self.logger = log_override or logger

    async def import_reference(
        self, source_ref: ExportReference, dest_ref: ExportReference
    ):
        self.logger.info(f"Importing reference {source_ref}")
        translated_ref = await self.translate_reference(source_ref)

        # Convert reference.columns into pandas DataFrame columns
        df = source_ref.columns.to_pandas()
        self.logger.info(f"Created DataFrame with columns: {df.dtypes}")

        # Convert duckdb types to pandas types
        self.logger.info(f"Converted DataFrame types: {df.dtypes}")

        # Generate random data for each column based on its type
        fake_data_size = 100
        for column_name, column_type in source_ref.columns.columns_as_pandas_dtypes():
            if column_type.upper() == "bool":
                df[column_name] = np.random.choice([True, False], size=fake_data_size)
            elif column_type.upper() in ["int", "int8", "int16", "int32", "int64"]:
                df[column_name] = np.random.randint(0, 100, size=fake_data_size)
            elif column_type.upper() in ["float", "float32", "float64"]:
                df[column_name] = np.random.random(size=fake_data_size)
            elif column_type.upper() == ["object"]:
                df[column_name] = np.random.choice(
                    ["oso", "random", "fake", "data", "foo", "bar", "baz"],
                    size=fake_data_size,
                )
            elif column_type.upper() in ["datetime64[ns]"]:
                df[column_name] = pd.to_datetime(
                    np.random.choice(
                        pd.date_range("2024-01-01", "2025-01-01", periods=100),
                        size=fake_data_size,
                    )
                )
            else:
                df[column_name] = np.random.choice(["unknown"], size=fake_data_size)

        # Write the DataFrame to a parquet file in the temporary directory
        parquet_file_path = translated_ref.payload["local_path"]
        df.to_parquet(parquet_file_path)
        self.logger.debug(f"Written DataFrame to parquet file: {parquet_file_path}")

        # Update the reference payload with the parquet file path
        source_ref.payload["parquet_file_path"] = parquet_file_path

    async def translate_reference(self, reference: ExportReference) -> ExportReference:
        self.logger.info(f"Translating reference {reference}")
        parquet_file_path = f"{self.temp_dir}/{reference.table.table_name}.parquet"
        return ExportReference(
            table=TableReference(table_name=reference.table.table_name),
            type=ExportType.LOCALFS,
            columns=reference.columns,
            payload={"local_path": parquet_file_path},
        )


class TrinoImportAdapter(DBImportAdapter):
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

    async def import_reference(
        self, source_ref: ExportReference, dest_ref: ExportReference
    ):
        self.logger.info(f"Importing reference {source_ref}")
        if source_ref.type != ExportType.GCS:
            raise NotImplementedError(f"Unsupported reference type {source_ref.type}")

        # Import the table from gcs into trino using the hive catalog
        import_path = source_ref.payload["gcs_path"]
        # If we are using a wildcard path, we need to remove the wildcard for
        # trino and keep a trailing slash
        if os.path.basename(import_path) == "*.parquet":
            import_path = f"{os.path.dirname(import_path)}/"
        elif import_path.endswith("/") or import_path.endswith("*"):
            import_path = f"{import_path[:-1]}/"

        base_create_query = f"""
            CREATE table "{dest_ref.table.catalog_name}"."{dest_ref.table.schema_name}"."{dest_ref.table.table_name}" (
                placeholder VARCHAR,
            ) WITH (
                format = 'PARQUET',
                external_location = '{import_path}'
            )
        """

        processed_columns = [
            self.process_columns_for_import(
                column_name,
                parse_one(
                    column_type,
                    dialect=source_ref.columns.dialect,
                    into=exp.DataType,
                ),
            )
            for column_name, column_type in source_ref.columns
        ]
        column_defs = [row[1] for row in processed_columns]

        create_query = parse_one(base_create_query)
        create_query.this.set("expressions", column_defs)
        await self.run_query(create_query.sql(dialect="trino"))

    def process_columns_for_import(
        self,
        column_name: str,
        column_type: exp.Expression,
    ) -> t.Tuple[exp.Identifier, exp.ColumnDef]:
        assert isinstance(
            column_type, exp.DataType
        ), "Column type must be an instance of DataType"

        self.logger.debug(f"processing column for import {column_name} {column_type}")

        # If the column to be exported is a date it will be output as an int64
        # but that will not work when we try to query the parquet files from
        # trino. So we will want to make sure that we import that as a
        # timestamp. We can cast it downstream.
        column_identifier = exp.to_identifier(column_name)
        processed_column_type = column_type
        # Assuming that we use polars or pyarrow at the time of parquet write.
        # It shouldn't be necessary to cast types.

        return (
            column_identifier,
            exp.ColumnDef(
                this=column_identifier,
                kind=processed_column_type,
            ),
        )

    async def translate_reference(self, reference: ExportReference) -> ExportReference:
        self.logger.info(f"Translating reference {reference}")
        if reference.type != ExportType.GCS:
            raise NotImplementedError(f"Unsupported reference type {reference.type}")

        return ExportReference(
            table=TableReference(
                catalog_name=self.hive_catalog,
                schema_name=self.hive_schema,
                table_name=reference.table.table_name,
            ),
            type=ExportType.TRINO,
            columns=reference.columns,
            payload={},
        )

    async def run_query(self, query: str):
        cursor = await self.db.cursor()
        self.logger.info(f"EXECUTING: {query}")
        await cursor.execute(query)
        return await cursor.fetchall()
