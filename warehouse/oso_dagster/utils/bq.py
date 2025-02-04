import typing as t
from dataclasses import dataclass

from google.cloud import bigquery
from google.cloud.bigquery import AccessEntry
from google.cloud.bigquery import Client as BQClient
from google.cloud.bigquery import DatasetReference, ExtractJobConfig
from google.cloud.bigquery.enums import EntityTypes
from google.cloud.bigquery.schema import SchemaField
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
    service_account: t.Optional[str]


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

        new_entries: t.List[AccessEntry] = []
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


def export_to_gcs(
    bq_client: BQClient, bq_table_config: BigQueryTableConfig, gcs_path: str
):
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
            # compression="ZSTD",
        ),
    )
    extract_job.result()
    return destination_uri


def get_table_schema(
    client: bigquery.Client, table_ref: bigquery.TableReference | str
) -> t.List[SchemaField]:
    """Fetches the schema of a table."""
    table = client.get_table(table_ref)
    return table.schema


SAFE_SCHEMA_MODIFICATIONS = [
    {"NUMERIC", "FLOAT", "DOUBLE"},
]

SAFE_SCHEMA_MODIFICATIONS_MAP: t.Dict[str, t.Set[str]] = {}
for group in SAFE_SCHEMA_MODIFICATIONS:
    for schema_type in group:
        SAFE_SCHEMA_MODIFICATIONS_MAP[schema_type] = group


def compare_schemas(
    schema1: t.List[SchemaField], schema2: t.List[SchemaField]
) -> t.Tuple[
    t.Dict[str, SchemaField],
    t.Dict[str, SchemaField],
    t.Dict[str, t.Dict[str, SchemaField]],
]:
    """Compares two BigQuery schemas and outputs the differences.

    Returns a tuple containing:
    - Fields only in schema1
    - Fields only in schema2
    - Fields present in both schemas but with different properties
    """
    schema1_fields: t.Dict[str, SchemaField] = {field.name: field for field in schema1}
    schema2_fields: t.Dict[str, SchemaField] = {field.name: field for field in schema2}

    # Fields only in schema1
    schema1_only: t.Dict[str, SchemaField] = {
        name: schema1_fields[name]
        for name in schema1_fields
        if name not in schema2_fields
    }

    # Fields only in schema2
    schema2_only: t.Dict[str, SchemaField] = {
        name: schema2_fields[name]
        for name in schema2_fields
        if name not in schema1_fields
    }

    # Fields in both schemas but with different properties
    modified_fields: t.Dict[str, t.Dict[str, SchemaField]] = {}
    for name in schema1_fields:
        if name in schema2_fields:
            if schema1_fields[name] != schema2_fields[name]:
                modified_fields[name] = {
                    "schema1": schema1_fields[name],
                    "schema2": schema2_fields[name],
                }

    return schema1_only, schema2_only, modified_fields


def compare_schemas_and_ignore_safe_changes(
    schema1: t.List[SchemaField], schema2: t.List[SchemaField]
) -> t.Tuple[
    t.Dict[str, SchemaField],
    t.Dict[str, SchemaField],
    t.Dict[str, t.Dict[str, SchemaField]],
]:
    schema1_only, schema2_only, modified = compare_schemas(schema1, schema2)

    delete_queue = []

    for field_name, modifications in modified.items():
        schema1_field = modifications["schema1"]
        schema2_field = modifications["schema2"]
        schema1_field_type = schema1_field.field_type or "__UNKNOWN__TYPE__"
        safe_group = SAFE_SCHEMA_MODIFICATIONS_MAP[schema1_field_type]
        if schema2_field.field_type in safe_group:
            delete_queue.append(field_name)

    for field_name in delete_queue:
        del modified[field_name]

    return schema1_only, schema2_only, modified


def print_schema_diff(
    schema1_only: t.Dict[str, SchemaField],
    schema2_only: t.Dict[str, SchemaField],
    modified_fields: t.Dict[str, t.Dict[str, SchemaField]],
) -> None:
    """Prints the schema differences."""
    if schema1_only:
        print("Fields only in Schema 1:")
        for field_name, field in schema1_only.items():
            print(f"  - {field_name}: {field.field_type}, {field.mode}")
    else:
        print("No fields unique to Schema 1.")

    if schema2_only:
        print("Fields only in Schema 2:")
        for field_name, field in schema2_only.items():
            print(f"  - {field_name}: {field.field_type}, {field.mode}")
    else:
        print("No fields unique to Schema 2.")

    if modified_fields:
        print("Fields with differences:")
        for field_name, fields in modified_fields.items():
            print(f"  - {field_name}:")
            print(
                f"    Schema 1: {fields['schema1'].field_type}, {fields['schema1'].mode}"
            )
            print(
                f"    Schema 2: {fields['schema2'].field_type}, {fields['schema2'].mode}"
            )
    else:
        print("No modified fields.")
