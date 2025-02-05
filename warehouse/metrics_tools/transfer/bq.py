import logging
import typing as t

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from metrics_tools.compute.types import ExportReference, ExportType, TableReference
from metrics_tools.transfer.base import ImporterInterface

logger = logging.getLogger(__name__)


class BigQueryImporter(ImporterInterface):
    def __init__(self, project_id: str):
        """
        Initializes the BigQueryImporter with a Google Cloud project ID.

        Args:
            project_id (str): The GCP project ID.
            dataset_prefix (str): Optional prefix for datasets.
        """

        self._client = bigquery.Client(project=project_id)

    def supported_types(self) -> t.Set[ExportType]:
        """
        Returns the set of supported export types for this importer.

        BigQuery supports GCS-based imports.
        """

        return {ExportType.GCS}

    async def import_table(
        self, destination_table: TableReference, export_reference: ExportReference
    ):
        """
        Imports a table from a Parquet file in GCS to BigQuery.

        Args:
            destination_table (TableReference): The destination table reference in BigQuery.
            export_reference (ExportReference): The export reference containing GCS path and metadata.
        """

        if export_reference.type != ExportType.GCS:
            raise ValueError("BigQueryImporter only supports GCS exports.")

        dataset_name = (
            f"{destination_table.schema_name or 'default'}"
        )
        table_id = (
            f"{self._client.project}.{dataset_name}.{destination_table.table_name}"
        )

        self._ensure_dataset_exists(dataset_name)

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        gcs_path = export_reference.payload.get("gcs_path")
        if not gcs_path:
            raise ValueError("GCS path is missing in the export reference payload.")

        logger.info(f"Starting import from {gcs_path} to {table_id}...")

        load_job = self._client.load_table_from_uri(
            gcs_path, table_id, job_config=job_config
        )

        load_job.result()

        logger.info(f"Import completed successfully for table {table_id}.")

    def _ensure_dataset_exists(self, dataset_name: str):
        """
        Ensures that a BigQuery dataset exists. Creates it if it doesn't exist.

        Args:
            dataset_name (str): The name of the dataset to check or create.
        """

        dataset_id = f"{self._client.project}.{dataset_name}"

        try:
            self._client.get_dataset(dataset_id)
            logger.info(f"Dataset {dataset_id} already exists.")
        except NotFound as _e:
            logger.info(f"Dataset {dataset_id} does not exist. Creating...")
            self._client.create_dataset(dataset_id)
            logger.info(f"Dataset {dataset_id} created successfully.")
