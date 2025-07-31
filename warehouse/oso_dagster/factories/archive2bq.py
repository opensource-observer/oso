import csv
import json
import os
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, TypeAlias, Union, cast

import pyarrow.parquet as pq
from dagster import AssetExecutionContext, MaterializeResult, asset
from dagster_gcp import BigQueryResource, GCSResource
from google.api_core.exceptions import NotFound
from google.cloud.bigquery import (
    LoadJobConfig,
    SchemaField,
    SourceFormat,
    WriteDisposition,
)
from oso_dagster.factories.common import AssetDeps, AssetFactoryResponse, GenericAsset
from oso_dagster.utils.gcs import batch_delete_folder

# The folder in the GCS bucket where we will stage the data
GCS_BUCKET_DIRECTORY = "archive2bq"
GCS_PROTOCOL = "gs://"

# The list of allowed types in BigQuery
BQ_ALLOWED_TYPES = [
    "STRING",
    "FLOAT",
    "FLOAT64",
    "INTEGER",
    "INT64",
    "TIMESTAMP",
    "DATETIME",
    "DATE",
    "BYTES",
    "BOOL",
    "BOOLEAN",
    "NUMERIC",
    "DECIMAL",
    "BIGNUMERIC",
    "BIGDECIMAL",
    "TIME",
    "JSON",
]

FieldTypeOverride: TypeAlias = str
FieldConfigOverride: TypeAlias = Dict[
    str, str
]  # {"type": "STRING", "mode": "NULLABLE"}
SchemaOverride: TypeAlias = Union[FieldTypeOverride, FieldConfigOverride]
SchemaOverridesDict: TypeAlias = Dict[str, SchemaOverride]
TableSchemaOverrides: TypeAlias = Dict[
    str, SchemaOverridesDict
]  # {table_name: {field_name: override}}


@dataclass(kw_only=True)
class Archive2BqAssetConfig:
    # The URL of the archive file
    source_url: str
    # The source format of the archive file
    source_format: str
    # The function to retrieve the files from the archive
    filter_fn: Optional[Callable[[str], bool]] = None
    # The maximum depth of the files in the archive
    max_depth: int = 3
    # The schema overrides for the BigQuery table
    # Format: {"table_name": {"field_name": "STRING" | {"type": "STRING", "mode": "NULLABLE"}}}
    # If None, BigQuery autodetect will be used. If specified, caller is responsible
    # for ensuring the schema matches the actual data structure in the files.
    schema_overrides: Optional[TableSchemaOverrides] = None
    # The GCS bucket to stage the data
    staging_bucket: str
    # The dataset in BigQuery
    dataset_id: str
    # Skip uncompression of archive files
    skip_uncompression: bool = False
    # Dagster key prefix
    key_prefix: Optional[str | List[str]] = ""
    # Dagster asset name
    asset_name: str
    # Dagster dependencies
    deps: AssetDeps
    # Combine all files into a single table (works for JSONL and CSV)
    combine_files: bool = False
    # Dagster remaining args
    asset_kwargs: dict = field(default_factory=lambda: {})


def cleanup_tempdir(tempdir: str):
    """
    Cleans up the temporary directory.

    Args:
        tempdir (str): The path to the temporary directory.

    Returns:
        None
    """
    shutil.rmtree(tempdir, ignore_errors=True)


def extract_to_tempdir(source_url: str, skip_uncompression: bool = False) -> str:
    """
    Extracts the source URL to the temporary directory using the extract function.

    Args:
        source_url (str): The URL of the archive file
        skip_uncompression (bool): Whether to skip uncompression of the archive

    Returns:
        str: The path to the temporary directory
    """
    tempdir = tempfile.mkdtemp()

    with urllib.request.urlopen(source_url) as response:
        file_name = os.path.basename(source_url)
        file_path = os.path.join(tempdir, file_name)
        with open(file_path, "wb") as f:
            f.write(response.read())

        if not skip_uncompression:
            shutil.unpack_archive(file_path, tempdir)

    return tempdir


def combine_jsonl_files(files: List[str], output_path: str) -> None:
    """Combines multiple JSONL files by concatenating them."""
    with open(output_path, "w", encoding="utf-8") as outfile:
        for file_path in files:
            outfile.write(Path(file_path).read_text(encoding="utf-8"))


def combine_csv_files(files: List[str], output_path: str) -> None:
    """Combines multiple CSV files, keeping only the first header."""
    with open(output_path, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        for i, file_path in enumerate(files):
            with open(file_path, "r", encoding="utf-8") as infile:
                reader = csv.reader(infile)
                if i > 0:
                    next(reader, None)
                writer.writerows(reader)


COMBINE_STRATEGIES = {
    SourceFormat.NEWLINE_DELIMITED_JSON: (combine_jsonl_files, ".jsonl"),
    SourceFormat.CSV: (combine_csv_files, ".csv"),
}


def get_list_of_files(
    tempdir: str, filter_fn: Optional[Callable[[str], bool]], max_depth: int
) -> List[str]:
    """
    Gets the list of files in the temporary directory, filtered by the filter function.

    Args:
        tempdir (str): The path to the temporary directory.
        filter_fn (Optional[Callable[[str], bool]]): A function that returns True for files to include. If None, all files are included.
        max_depth (int): The maximum depth of files to search.

    Returns:
        List[str]: The list of files matching the filter function.
    """
    files = []
    base_depth = tempdir.rstrip(os.sep).count(os.sep)

    for root, _, filenames in os.walk(tempdir):
        current_depth = root.rstrip(os.sep).count(os.sep) - base_depth
        if current_depth > max_depth:
            continue

        for filename in filenames:
            file_path = os.path.join(root, filename)
            if filter_fn is None or filter_fn(file_path):
                files.append(file_path)

    return files


def create_dataset_if_not_exists(
    context: AssetExecutionContext, bigquery: BigQueryResource, dataset_id: str
) -> None:
    """
    Creates the dataset in BigQuery if it does not exist.

    Args:
        bigquery (BigQueryResource): The BigQuery resource.
        context (AssetExecutionContext): The asset execution context.
        dataset_id (str): The dataset ID.

    Returns:
        None
    """
    with bigquery.get_client() as bq_client:
        dataset_ref = bq_client.dataset(dataset_id)
        try:
            bq_client.get_dataset(dataset_ref)
        except NotFound:
            context.log.info(f"Creating dataset {dataset_id}")
            bq_client.create_dataset(dataset_ref)


def get_csv_schema(file_path: str) -> List[SchemaField]:
    """
    Gets the schema of the CSV file.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        List[SchemaField]: The schema of the CSV file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

    return [SchemaField(name, "STRING") for name in header]


def get_parquet_schema(file_path: str) -> List[SchemaField]:
    """
    Gets the schema of the Parquet file.

    Args:
        file_path (str): The path to the Parquet file.

    Returns:
        List[SchemaField]: The schema of the Parquet file.
    """
    parquet_file = pq.ParquetFile(file_path)
    schema = parquet_file.schema_arrow
    return [SchemaField(field.name, "STRING") for field in schema]


def get_jsonl_schema(file_path: str) -> List[SchemaField]:
    """
    Gets a rudimentary schema of the JSONL file by reading the first line.

    WARNING: Simplified schema detection with limitations:
    - Only reads first line, assumes all fields are strings
    - May miss optional fields in later records
    - Caller responsible for ensuring schema overrides match actual data

    Args:
        file_path (str): Path to the JSONL file.

    Returns:
        List[SchemaField]: Basic schema with all fields as STRING type.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        if not first_line:
            raise ValueError(f"JSONL file {file_path} is empty")

        try:
            first_record = json.loads(first_line)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in first line of {file_path}: {e}") from e

        if not isinstance(first_record, dict) or not first_record:
            raise ValueError(
                f"JSONL file {file_path} must contain non-empty JSON objects, "
                f"got {type(first_record).__name__}"
            )

        return [SchemaField(key, "STRING") for key in first_record.keys()]


def upload_file_to_gcs(
    context: AssetExecutionContext,
    gcs: GCSResource,
    staging_bucket: str,
    file_path: str,
    sync_id: str,
) -> str:
    """
    Uploads the file to the GCS staging bucket.

    Args:
        context (AssetExecutionContext): The asset execution context.
        gcs (GCSResource): The GCS resource.
        staging_bucket (str): The GCS staging bucket.
        file_path (str): The path to the file.
        sync_id (str): The sync ID.

    Returns:
        str: GCS path to the uploaded file.
    """
    client = gcs.get_client()
    bucket_name = staging_bucket.replace(GCS_PROTOCOL, "")
    bucket = client.bucket(bucket_name, user_project=gcs.project)
    blob = bucket.blob(
        f"{GCS_BUCKET_DIRECTORY}/{sync_id}/{os.path.basename(file_path)}"
    )
    blob.upload_from_filename(file_path)
    context.log.info(f"Archive2Bq: Uploaded {file_path} to GCS at {blob.public_url}")

    return f"gs://{bucket_name}/{blob.name}"


def apply_schema_overrides(
    schema: List[SchemaField],
    schema_overrides: Dict[str, str | Dict[str, str]],
) -> List[SchemaField]:
    """
    Applies the schema overrides to the schema.

    Args:
        schema (List[SchemaField]): The schema.
        schema_overrides (Dict[str, str | Dict[str, str]]): The schema overrides.
            Can be either a string for field type, or a dict with 'type' and 'mode' keys.

    Returns:
        List[SchemaField]: The schema with the overrides applied.
    """
    for field_name, override in schema_overrides.items():
        field_type, field_mode = (
            (override, "NULLABLE")
            if isinstance(override, str)
            else (override.get("type", "STRING"), override.get("mode", "NULLABLE"))
        )

        if field_type not in BQ_ALLOWED_TYPES:
            raise ValueError(f"Invalid field type: {field_type}")

        for i, param in enumerate(schema):
            if param.name == field_name:
                schema[i] = SchemaField(param.name, field_type, mode=field_mode)
                break

    return schema


def upload_file_to_bq(
    bigquery: BigQueryResource,
    gcs: GCSResource,
    context: AssetExecutionContext,
    asset_config: Archive2BqAssetConfig,
    file_path: str,
    sync_id: str,
) -> None:
    """
    Uploads the file to the GCS staging bucket.

    Args:
        bigquery (BigQueryResource): The BigQuery resource.
        asset_config (Archive2BqAssetConfig): The asset configuration.
        file_path (str): The path to the file.
        sync_id (str): The sync ID.

    Returns:
        None
    """
    gcs_url = upload_file_to_gcs(
        context,
        gcs,
        asset_config.staging_bucket,
        file_path,
        sync_id,
    )

    destination_table_name = os.path.splitext(os.path.basename(file_path))[0]

    schema_extractors = {
        SourceFormat.CSV: get_csv_schema,
        SourceFormat.PARQUET: get_parquet_schema,
        SourceFormat.NEWLINE_DELIMITED_JSON: get_jsonl_schema,
    }

    def make_csv_config(schema=None):
        return LoadJobConfig(
            schema=schema,
            autodetect=schema is None,
            skip_leading_rows=1,
            source_format=SourceFormat.CSV,
            allow_quoted_newlines=True,
            write_disposition=WriteDisposition.WRITE_TRUNCATE,
        )

    def make_default_config(source_format, schema=None):
        return LoadJobConfig(
            schema=schema,
            autodetect=schema is None,
            source_format=source_format,
            write_disposition=WriteDisposition.WRITE_TRUNCATE,
        )

    config_makers = {
        SourceFormat.CSV: make_csv_config,
        SourceFormat.PARQUET: lambda schema=None: make_default_config(
            SourceFormat.PARQUET, schema
        ),
        SourceFormat.NEWLINE_DELIMITED_JSON: lambda schema=None: make_default_config(
            SourceFormat.NEWLINE_DELIMITED_JSON, schema
        ),
    }

    with bigquery.get_client() as bq_client:
        table_id = f"{asset_config.dataset_id}.{destination_table_name}"

        if asset_config.source_format not in schema_extractors:
            raise ValueError(f"Unsupported source format: {asset_config.source_format}")

        table_overrides = (asset_config.schema_overrides or {}).get(
            destination_table_name, {}
        )

        schema = (
            apply_schema_overrides(
                schema_extractors[asset_config.source_format](file_path),
                table_overrides,
            )
            if table_overrides
            else None
        )

        job_config = config_makers[asset_config.source_format](schema)

        load_job = bq_client.load_table_from_uri(
            gcs_url, table_id, job_config=job_config
        )

        load_job.result()

        context.log.info(f"Archive2Bq: {table_id} loaded with job ID {load_job.job_id}")


def delete_gcs_files(
    gcs: GCSResource,
    asset_config: Archive2BqAssetConfig,
    sync_id: str,
) -> None:
    """
    Deletes the GCS files in the staging bucket.

    Args:
        gcs (GCSResource): The GCS resource.
        asset_config (Archive2BqAssetConfig): The asset configuration.
        sync_id (str): The sync ID.
    """
    gcs_bucket_url = (
        asset_config.staging_bucket
        if asset_config.staging_bucket.startswith(GCS_PROTOCOL)
        else GCS_PROTOCOL + asset_config.staging_bucket
    )
    gcs_bucket_url = gcs_bucket_url.rstrip("/")

    gcs_bucket_name = gcs_bucket_url.replace(GCS_PROTOCOL, "")

    gcs_relative_dir = f"{GCS_BUCKET_DIRECTORY}/{sync_id}"

    gcs_client = gcs.get_client()
    batch_delete_folder(
        gcs_client, gcs_bucket_name, gcs_relative_dir, user_project=gcs.project
    )


def create_archive2bq_asset(
    asset_config: Archive2BqAssetConfig,
) -> AssetFactoryResponse:
    """
    Creates a Dagster asset that copies an archive file into BigQuery.

    Args:
        asset_config (Archive2BqAssetConfig): The asset configuration.

    Returns:
        AssetFactoryResponse: The asset factory response.
    """
    tags = {
        "opensource.observer/factory": "archive2bq",
    }

    if asset_config.source_format not in [
        SourceFormat.CSV,
        SourceFormat.PARQUET,
        SourceFormat.NEWLINE_DELIMITED_JSON,
    ]:
        raise ValueError(f"Unsupported source format: {asset_config.source_format}")

    @asset(
        name=asset_config.asset_name,
        key_prefix=asset_config.key_prefix,
        tags=tags,
        deps=asset_config.deps,
        **asset_config.asset_kwargs,
    )
    def archive2bq_asset(
        context: AssetExecutionContext,
        bigquery: BigQueryResource,
        gcs: GCSResource,
    ) -> MaterializeResult:
        context.log.info(
            f"Materializing asset {asset_config.key_prefix}/{asset_config.asset_name}"
        )

        tempdir = extract_to_tempdir(
            asset_config.source_url, asset_config.skip_uncompression
        )

        context.log.info(
            f"Archive2Bq: Extracted {asset_config.source_url} to {tempdir}"
        )

        files = get_list_of_files(
            tempdir,
            asset_config.filter_fn,
            asset_config.max_depth,
        )

        context.log.info(
            f"Archive2Bq: Found {len(files)} valid files: {', '.join(files)}"
        )

        if len(files) == 0:
            cleanup_tempdir(tempdir)
            raise ValueError("No valid files found in the archive")

        all_files = sorted(
            [os.path.splitext(os.path.basename(file))[0] for file in files]
        )

        if len(all_files) != len(set(all_files)):
            cleanup_tempdir(tempdir)
            raise ValueError("Files must have unique names")

        create_dataset_if_not_exists(context, bigquery, asset_config.dataset_id)

        if (
            asset_config.combine_files
            and asset_config.source_format in COMBINE_STRATEGIES
        ):
            combine_fn, ext = COMBINE_STRATEGIES[asset_config.source_format]
            combined_path = os.path.join(tempdir, f"{asset_config.asset_name}{ext}")
            combine_fn(files, combined_path)
            files_to_process = [combined_path]
        else:
            files_to_process = files

        for file in files_to_process:
            upload_file_to_bq(
                bigquery, gcs, context, asset_config, file, context.run_id
            )

        cleanup_tempdir(tempdir)
        delete_gcs_files(gcs, asset_config, context.run_id)

        return MaterializeResult(
            metadata={
                "success": True,
                "asset": asset_config.asset_name,
                "datasets": [
                    f"{asset_config.dataset_id}.{os.path.basename(file)}"
                    for file in files
                ],
            }
        )

    # https://github.com/opensource-observer/oso/issues/2403
    return AssetFactoryResponse([cast(GenericAsset, archive2bq_asset)])
