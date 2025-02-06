import logging
import os
import typing as t
import uuid
from datetime import datetime
from urllib.parse import urlparse

import duckdb
from google.cloud import storage
from metrics_tools.compute.types import (
    ColumnsDefinition,
    ExportReference,
    ExportType,
    TableReference,
)
from metrics_tools.transfer.base import ExporterInterface, ImporterInterface
from metrics_tools.transfer.storage import TimeOrderedStorage
from sqlglot import exp

logger = logging.getLogger(__name__)


class DuckDBExporter(ExporterInterface):
    def __init__(
        self,
        time_ordered_storage: TimeOrderedStorage,
        connection: duckdb.DuckDBPyConnection,
        log_override: t.Optional[logging.Logger] = None,
        gcs_bucket_name: t.Optional[str] = None,
    ):
        """
        Initializes the DuckDBExporter with a TimeOrderedStorage instance
        and a DuckDB connection.

        Args:
            time_ordered_storage (TimeOrderedStorage): The TimeOrderedStorage instance.
            connection (duckdb.DuckDBPyConnection): The DuckDB connection.
            log_override (t.Optional[logging.Logger]): Optional logger override.
            gcs_bucket_name (t.Optional[str]): Optional GCS bucket name for uploads.
        """

        self.time_ordered_storage = time_ordered_storage
        self.connection = connection
        self.logger = log_override or logger
        self.gcs_bucket_name = gcs_bucket_name

        if self.gcs_bucket_name:
            self.storage_client = storage.Client()
        else:
            self.storage_client = None

    def process_columns(
        self, column_name: str, column_type: exp.Expression
    ) -> t.Tuple[exp.Identifier, exp.ColumnDef, exp.Expression]:
        """
        Processes a column definition and returns the column identifier,
        column definition, and column select expression.

        Args:
            column_name (str): The column name.
            column_type (exp.Expression): The column type expression.
        """

        assert isinstance(
            column_type, exp.DataType
        ), "column_type must parse into DataType"

        self.logger.debug(
            f"Creating column def for column_name: {column_name} column_type: {column_type}"
        )
        column_select = exp.to_identifier(column_name)
        column_identifier = exp.to_identifier(column_name)

        return (
            column_identifier,
            exp.ColumnDef(this=column_identifier, kind=column_type),
            column_select,
        )

    def run_query(self, query: str):
        """
        Runs a query on the DuckDB connection.

        Args:
            query (str): The SQL query to execute.
        """

        self.logger.info(f"Executing SQL: {query}")
        return self.connection.execute(query)

    async def export_table(
        self,
        table: TableReference,
        supported_types: t.Set[ExportType],
        export_time: t.Optional[datetime] = None,
    ) -> ExportReference:
        """
        Exports a table to a file and optionally uploads to GCS.

        Args:
            table (TableReference): The table reference to export.
            supported_types (t.Set[ExportType]): The set of supported export types.
            export_time (t.Optional[datetime]): The export time.
        """

        if not ({ExportType.LOCALFS, ExportType.GCS} & supported_types):
            raise ValueError("DuckDB only supports local file and GCS exports")

        export_time = export_time or datetime.now()
        col_result = self.run_query(f"DESCRIBE {table.fqn}").fetchall()

        columns: t.List[t.Tuple[str, str]] = [(row[0], row[1]) for row in col_result]

        export_table_name = f"export_{table.table_name}_{uuid.uuid4().hex}"
        local_file_path = self.local_export_path(export_table_name)

        export_query = (
            f"COPY (SELECT * FROM {table.fqn}) TO '{local_file_path}' (FORMAT PARQUET)"
        )
        self.run_query(export_query)

        gcs_path = None
        if ExportType.GCS in supported_types and self.gcs_bucket_name:
            gcs_path = await self.upload_to_gcs(local_file_path, export_table_name)

        return ExportReference(
            table=TableReference(table_name=table.table_name),
            type=ExportType.GCS if gcs_path else ExportType.LOCALFS,
            payload=(
                {"file_path": local_file_path, "gcs_path": gcs_path}
                if gcs_path
                else {"file_path": local_file_path}
            ),
            columns=ColumnsDefinition(columns=columns, dialect="duckdb"),
        )

    def local_export_path(self, export_table_name: str) -> str:
        """
        Generates a local path for file export

        Args:
            export_table_name (str): The name of the exported table.
        """

        export_dir = "/tmp/_duckdb_exports"
        os.makedirs(export_dir, exist_ok=True)
        return os.path.join(export_dir, f"{export_table_name}.parquet")

    def export_path(self, export_time: datetime, export_table_name: str) -> str:
        """
        Generates a path for file export

        Args:
            export_time (datetime): The export time.
            export_table_name (str): The name of the exported table.
        """

        return self.time_ordered_storage.generate_path(
            export_time, f"{export_table_name}.parquet"
        )

    async def upload_to_gcs(self, file_path: str, export_table_name: str) -> str:
        """
        Uploads a file to Google Cloud Storage.

        Args:
            file_path (str): The local path to the file to upload.
            export_table_name (str): The name of the exported table for the GCS path.

        Returns:
            str: The GCS URI of the uploaded file.
        """

        if not self.storage_client or not self.gcs_bucket_name:
            raise ValueError("GCS storage client or bucket name not configured.")

        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        blob_path = f"exports/{export_table_name}.parquet"
        blob = bucket.blob(blob_path)

        self.logger.info(f"Uploading {file_path} to GCS at {blob_path}...")
        blob.upload_from_filename(file_path)
        gcs_uri = f"gs://{self.gcs_bucket_name}/{blob_path}"

        self.logger.info(f"File successfully uploaded to GCS: {gcs_uri}")
        return gcs_uri

    async def cleanup_ref(self, export_reference: ExportReference):
        """
        Cleans up a file associated with an export reference.

        Args:
            export_reference (ExportReference): The export reference.
        """

        file_path = export_reference.payload.get("file_path")
        if file_path:
            self.logger.debug(f"Deleting file: {file_path}")
            try:
                os.remove(file_path)
            except FileNotFoundError:
                self.logger.warning(f"File {file_path} not found for deletion")

    async def cleanup_expired(self, expiration: datetime, dry_run: bool = False):
        """
        Cleans up expired files in the storage.

        Args:
            expiration (datetime): The expiration time.
            dry_run (bool): Whether to perform a dry run.
        """

        count = 0

        for f in self.time_ordered_storage.iter_files(before=expiration):
            if not dry_run:
                self.logger.debug(f"Deleting: {f.uri}")
                f.delete()
            else:
                self.logger.debug(f"Would have deleted: {f.uri}")
            count += 1

        if count == 0:
            self.logger.debug("No expired files found")


class DuckDBImporter(ImporterInterface):
    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        log_override: t.Optional[logging.Logger] = None,
    ):
        """
        Initializes the DuckDBImporter with a DuckDB connection and a GCS client.

        Args:
            connection (duckdb.DuckDBPyConnection): The DuckDB connection.
            log_override (t.Optional[logging.Logger]): Optional logger override.
        """

        self.connection = connection
        self.logger = log_override or logger
        self.storage_client = storage.Client()
        self.local_import_dir = "/tmp/_duckdb_imports"
        os.makedirs(self.local_import_dir, exist_ok=True)

    def supported_types(self) -> t.Set[ExportType]:
        """
        Returns the set of supported export types for this importer.
        DuckDBImporter only supports GCS-based exports.
        """

        return {ExportType.GCS}

    def download_from_gcs(self, gcs_uri: str) -> str:
        """
        Downloads the file from the provided GCS URI to a local temporary location.

        Args:
            gcs_uri (str): The GCS URI (e.g. "gs://<bucket>/<path>") to download.

        Returns:
            str: The local file path where the file was downloaded.
        """

        parsed = urlparse(gcs_uri)
        bucket_name = parsed.netloc
        blob_path = parsed.path.lstrip("/")
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        local_file = os.path.join(self.local_import_dir, f"{uuid.uuid4().hex}.parquet")
        self.logger.info(f"Downloading {gcs_uri} to {local_file}...")
        blob.download_to_filename(local_file)
        self.logger.info(f"Downloaded file to {local_file}.")
        return local_file

    async def import_table(
        self, destination_table: TableReference, export_reference: ExportReference
    ):
        """
        Imports a table into DuckDB from a Parquet file stored on GCS.

        The method downloads the file from GCS, drops the destination table if it exists,
        and creates a new table using DuckDB's read_parquet() function.

        Args:
            destination_table (TableReference): The target table reference in DuckDB.
            export_reference (ExportReference): The export metadata which must include a valid "gcs_path".

        Raises:
            ValueError: If export_reference does not specify a GCS export.
        """

        if export_reference.type != ExportType.GCS:
            raise ValueError("DuckDBImporter only supports GCS exports.")

        gcs_path = export_reference.payload.get("gcs_path")
        if not gcs_path:
            raise ValueError("GCS path is missing in the export reference payload.")

        local_file_path = self.download_from_gcs(gcs_path)
        try:
            self.logger.debug(f"Dropping table {destination_table.fqn}...")
            self.connection.execute(f"DROP TABLE IF EXISTS {destination_table.fqn}")

            self.logger.debug(
                f"Creating table {destination_table.fqn} from {local_file_path}..."
            )
            create_sql = (
                f"CREATE TABLE {destination_table.fqn} AS "
                f"SELECT * FROM read_parquet('{local_file_path}')"
            )
            self.connection.execute(create_sql)
            self.logger.info(
                f"Table {destination_table.fqn} imported successfully in DuckDB."
            )
        finally:
            self.logger.debug(f"Deleting temporary file {local_file_path}...")
            try:
                os.remove(local_file_path)
                self.logger.debug("Temporary file deleted successfully.")
            except Exception as e:
                self.logger.warning(
                    f"Failed to delete temporary file {local_file_path}: {e}"
                )

    async def cleanup_ref(self, export_reference: ExportReference):
        """
        This importer does not retain external state that requires cleanup.
        Temporary files are removed immediately after table creation.
        """

        self.logger.debug("No additional cleanup required for DuckDBImporter.")
