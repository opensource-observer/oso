from typing import List, Optional
from dataclasses import dataclass

from google.cloud.bigquery import DatasetReference, AccessEntry, Client as BQClient, ExtractJobConfig
from google.cloud.bigquery.enums import EntityTypes
from google.cloud.exceptions import NotFound, PreconditionFailed
from .retry import retry

# Configuration for a BigQuery Dataset
@dataclass(kw_only=True)
class BigQueryDatasetConfig:
    # GCP project ID
    project_id: str
    # BigQuery dataset
    dataset_name: str
    # Service account
    service_account: Optional[str]

@dataclass(kw_only=True)
class BigQueryTableConfig(BigQueryDatasetConfig):
    # BigQuery table
    table_name: str

@dataclass
class DatasetOptions:
    dataset_ref: DatasetReference
    is_public: bool = False

def ensure_dataset(client: BQClient, options: DatasetOptions):
    """
    Create a public dataset if missing
    This will automatically add `allAuthenticatedUsers` with read-only access

    Parameters
    ----------
    client: BQClient
        The Google BigQuery client
    options: DatasetOptions
    """
    
    try:
        client.get_dataset(options.dataset_ref)
    except NotFound:
        client.create_dataset(options.dataset_ref)

    def retry_update():
        # Manage the public settings for this dataset
        dataset = client.get_dataset(options.dataset_ref)
        access_entries = dataset.access_entries
        for entry in access_entries:
            # Do nothing if the expected entity already has the correct access
            if entry.entity_id == "allAuthenticatedUsers" and entry.role == "READER":
                return

        new_entries: List[AccessEntry] = []
        if options.is_public:
            new_entries.append(
                AccessEntry(
                    role="READER",
                    entity_type=EntityTypes.SPECIAL_GROUP.value,
                    entity_id="allAuthenticatedUsers",
                )
            )
        new_entries.extend(access_entries)
        dataset.access_entries = new_entries
        client.update_dataset(dataset, ["access_entries"])

    def error_handler(exc: Exception):
        if type(exc) != PreconditionFailed:
            raise exc

    retry(retry_update, error_handler)

def export_to_gcs(bq_client: BQClient, bq_table_config: BigQueryTableConfig, gcs_path: str):
    """
    Export a BigQuery table to partitioned CSV files in GCS

    Parameters
    ----------
    bq_client: BQClient
        BigQuery client
    bq_table_config: BigQueryTableConfig
        BigQuery table configuration
    gcs_path: str
        GCS path to export to

    Returns
    -------
    str
        gcs_path
    """
    dataset_ref = bq_client.dataset(dataset_id=bq_table_config.dataset_name)
    table_ref = dataset_ref.table(bq_table_config.table_name)
    destination_uri = f"{gcs_path}/*.parquet"
    # Reference:
    # https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.job.ExtractJobConfig
    extract_job = bq_client.extract_table(
        table_ref,
        destination_uri,
        location="US",
        # When importing into Clickhouse, note the conventions used for compression
        # https://clickhouse.com/docs/en/sql-reference/table-functions/s3
        job_config=ExtractJobConfig(
            print_header=False,
            destination_format="PARQUET",
            #compression="ZSTD",
        ),
    )
    extract_job.result()
    return destination_uri