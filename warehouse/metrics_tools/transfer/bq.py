import logging
import typing as t
from itertools import batched

from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound
from metrics_service.types import ExportReference, ExportType, TableReference
from metrics_tools.transfer.base import ImporterInterface

logger = logging.getLogger(__name__)

BIGQUERY_BATCH_SIZE = 10000


class BigQueryImporter(ImporterInterface):
    def __init__(self, project_id: str):
        """
        Initializes the BigQueryImporter with a Google Cloud project ID.

        Args:
            project_id (str): The GCP project ID.
            dataset_prefix (str): Optional prefix for datasets.
        """

        self._client = bigquery.Client(project=project_id)
        self._storage_client = storage.Client(project=project_id)

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
        Imports a table from a GCS export to BigQuery.

        Args:
            destination_table (TableReference): The BigQuery table to import to.
            export_reference (ExportReference): The export reference containing the GCS path.
        """

        if export_reference.type != ExportType.GCS:
            raise ValueError("BigQueryImporter only supports GCS exports.")

        dataset_name = destination_table.schema_name or "default"
        table_id = (
            f"{self._client.project}.{dataset_name}.{destination_table.table_name}"
        )
        self._ensure_dataset_exists(dataset_name)

        gcs_path = export_reference.payload.get("gcs_path")
        if not gcs_path:
            raise ValueError("GCS path is missing in the export reference payload.")

        gcs_bucket_name, gcs_prefix = self._parse_gcs_path(gcs_path)
        bucket = self._storage_client.bucket(gcs_bucket_name)
        blobs = list(bucket.list_blobs(prefix=gcs_prefix))

        source_uris = [f"gs://{gcs_bucket_name}/{blob.name}" for blob in blobs]
        if not source_uris:
            raise ValueError(f"No files found in GCS path {gcs_path}")

        if len(source_uris) > BIGQUERY_BATCH_SIZE:
            logger.info(
                f"Large number of source files detected ({len(source_uris)}). "
                f"Processing in batches of {BIGQUERY_BATCH_SIZE} to respect BigQuery limits."
            )

            total_batches = (
                len(source_uris) + BIGQUERY_BATCH_SIZE - 1
            ) // BIGQUERY_BATCH_SIZE

            for batch_num, batch in enumerate(
                batched(source_uris, BIGQUERY_BATCH_SIZE), 1
            ):
                logger.info(
                    f"Processing batch {batch_num}/{total_batches}: {len(batch)} files"
                )

                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.PARQUET,
                    autodetect=True,
                    write_disposition=(
                        bigquery.WriteDisposition.WRITE_TRUNCATE
                        if batch_num == 1
                        else bigquery.WriteDisposition.WRITE_APPEND
                    ),
                )

                load_job = self._client.load_table_from_uri(
                    batch, table_id, job_config=job_config
                )

                load_job.result()
                logger.info(f"Batch {batch_num} import completed successfully.")
        else:
            logger.info(
                f"Importing {len(source_uris)} files from directory {gcs_path} to {table_id}"
            )

            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
                autodetect=True,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )

            load_job = self._client.load_table_from_uri(
                source_uris, table_id, job_config=job_config
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
        except NotFound:
            logger.info(f"Dataset {dataset_id} does not exist. Creating...")
            self._client.create_dataset(dataset_id)
            logger.info(f"Dataset {dataset_id} created successfully.")

    def _parse_gcs_path(self, gcs_path: str) -> t.Tuple[str, str]:
        """Extracts bucket and prefix from GCS path."""

        if not gcs_path.startswith("gs://"):
            raise ValueError("Invalid GCS path. Must start with 'gs://'")

        path_parts = gcs_path[5:].split("/", 1)
        bucket_name = path_parts[0]
        prefix = path_parts[1] if len(path_parts) > 1 else ""
        return bucket_name, prefix
