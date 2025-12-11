import re
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, cast

import arrow
from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    DefaultSensorStatus,
    EventLogEntry,
    MaterializeResult,
    OpExecutionContext,
    RunConfig,
    RunRequest,
    SensorEvaluationContext,
    asset,
    asset_sensor,
    job,
    op,
)
from dagster_gcp import BigQueryResource, GCSResource
from google.api_core.exceptions import NotFound
from google.cloud.bigquery.job import CopyJobConfig

from ..utils import (
    DatasetOptions,
    SourceMode,
    TimeInterval,
    add_key_prefix_as_tag,
    add_tags,
    ensure_dataset,
)
from .common import AssetFactoryResponse, GenericAsset


@dataclass(kw_only=True)
class BaseGCSAsset:
    # Dagster key prefix
    key_prefix: Optional[str | Sequence[str]] = ""
    # Dagster asset name
    name: str
    # GCP project ID (usually opensource-observer)
    project_id: str
    # GCS bucket name
    bucket_name: str
    path_base: str
    # Regex for incoming files
    file_match: str
    # Table name nested under the dataset
    destination_table: str
    # BigQuery temporary staging dataset for imports
    raw_dataset_name: str
    # BigQuery destination dataset
    clean_dataset_name: str
    # Format of incoming files (PARQUET preferred)
    format: str = "CSV"
    # Dagster remaining arguments
    asset_kwargs: dict = field(default_factory=lambda: {})

    tags: Dict[str, str] = field(default_factory=lambda: {})

    environment: str = "production"


@dataclass(kw_only=True)
class IntervalGCSAsset(BaseGCSAsset):
    # How often we should run this job
    interval: TimeInterval
    # Incremental or overwrite
    mode: SourceMode
    # Retention time before deleting GCS files
    retention_days: int


def parse_interval_prefix(interval: TimeInterval, prefix: str) -> arrow.Arrow:
    return arrow.get(prefix, "YYYYMMDD")


def interval_gcs_import_asset(config: IntervalGCSAsset):
    # Find all of the "intervals" in the bucket and load them into the `raw_sources` dataset
    # Run these sources through a secondary dbt model into `clean_sources`

    tags = {
        "opensource.observer/factory": "gcs",
        "opensource.observer/environment": config.environment,
    }

    # Extend with additional tags
    tags.update(config.tags)

    tags = add_key_prefix_as_tag(tags, config.key_prefix)

    @asset(
        name=config.name,
        key_prefix=config.key_prefix,
        tags=add_tags(
            tags,
            {
                "opensource.observer/type": "source",
                "opensource.observer/source": "stable",
            },
        ),
        compute_kind="gcs",
        **config.asset_kwargs,
    )
    def gcs_asset(
        context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
    ) -> MaterializeResult:
        # Check the current state of the bigquery db (we will only load things
        # that are new than that). We continously store the imported data in
        # {project}.{dataset}.{table}_{interval_prefix}.
        with bigquery.get_client() as bq_client:
            ensure_dataset(
                bq_client,
                DatasetOptions(
                    dataset_ref=bq_client.dataset(dataset_id=config.clean_dataset_name),
                    is_public=True,
                ),
            )

            clean_dataset = bq_client.get_dataset(config.clean_dataset_name)
            clean_table_ref = clean_dataset.table(config.destination_table)

            current_source_date = arrow.get("1970-01-01")
            try:
                clean_table = bq_client.get_table(clean_table_ref)
                current_source_date = arrow.get(
                    clean_table.labels.get("source_date", "1970-01-01")
                )
            except NotFound as exc:
                if config.destination_table in exc.message:
                    context.log.info("Cleaned destination table not found.")
                else:
                    raise exc

            client = gcs.get_client()
            bucket = client.bucket(config.bucket_name, user_project=gcs.project)
            blobs = bucket.list_blobs(match_glob=f"{config.path_base}/**")

            file_matcher = re.compile(config.path_base + "/" + config.file_match)

            matching_blobs = []

            # List all of the files in the prefix
            for blob in blobs:
                match = file_matcher.match(blob.name)
                if not match:
                    context.log.debug(f"skipping {blob.name}")
                    continue
                try:
                    interval_timestamp = arrow.get(
                        match.group("interval_timestamp"), "YYYY-MM-DD"
                    )
                    matching_blobs.append((interval_timestamp, blob.name))
                except IndexError:
                    context.log.debug(f"skipping {blob.name}")
                    continue

            sorted_blobs = sorted(
                matching_blobs, key=lambda a: a[0].int_timestamp, reverse=True
            )

            if len(sorted_blobs) == 0:
                context.log.info("no existing data found")
                return MaterializeResult(
                    metadata={
                        "updated": False,
                        "files_loaded": 0,
                        "latest_source_date": current_source_date.format("YYYY-MM-DD"),
                    }
                )

            latest_source_date = sorted_blobs[0][0]

            if latest_source_date.int_timestamp <= current_source_date.int_timestamp:
                context.log.info("no updated data found")

                return MaterializeResult(
                    metadata={
                        "updated": False,
                        "files_loaded": 0,
                        "latest": current_source_date.format("YYYY-MM-DD"),
                    }
                )

            blob_name = sorted_blobs[0][1]

            interval_table = f"{config.project_id}.{config.raw_dataset_name}.{config.destination_table}__{latest_source_date.format('YYYYMMDD')}"

            # Run the import of the latest data and overwrite the data
            bq_client.query_and_wait(
                f"""
            LOAD DATA OVERWRITE `{interval_table}`
            FROM FILES (
                format = "{config.format}",
                uris = ["gs://{config.bucket_name}/{blob_name}"]
            );
            """
            )

            raw_table_ref = bq_client.get_dataset(config.raw_dataset_name).table(
                f"{config.destination_table}__{latest_source_date.format('YYYYMMDD')}"
            )

            copy_job_config = CopyJobConfig(write_disposition="WRITE_TRUNCATE")

            # The clean table is just the overwritten data without any date.
            # We keep old datasets around in case we need to rollback for any reason.
            job = bq_client.copy_table(
                raw_table_ref,
                clean_table_ref,
                location="US",
                job_config=copy_job_config,
            )
            job.result()

            latest_source_date_str = latest_source_date.format("YYYY-MM-DD")

            clean_table = bq_client.get_table(clean_table_ref)
            labels = clean_table.labels
            labels["source_date"] = latest_source_date_str
            clean_table.labels = labels
            bq_client.update_table(clean_table, fields=["labels"])

            return MaterializeResult(
                metadata={
                    "updated": True,
                    "files_loaded": 1,
                    "latest_source_date": latest_source_date_str,
                }
            )

    asset_config = config

    @op(name=f"{config.name}_clean_up_op", tags=tags)
    def gcs_clean_up_op(context: OpExecutionContext, config: dict):
        context.log.info(f"Running clean up for {asset_config.name}")

    @job(name=f"{config.name}_clean_up_job", tags=tags)
    def gcs_clean_up_job():
        gcs_clean_up_op()

    @asset_sensor(
        asset_key=cast(AssetsDefinition, gcs_asset).key,
        name=f"{config.name}_clean_up_sensor",
        job=gcs_clean_up_job,
        default_status=DefaultSensorStatus.STOPPED,
    )
    def gcs_clean_up_sensor(
        context: SensorEvaluationContext, _gcs: GCSResource, asset_event: EventLogEntry
    ):
        yield RunRequest(
            run_key=context.cursor,
            run_config=RunConfig(
                ops={
                    f"{config.name}_clean_up_op": {
                        "op_config": {"asset_event": asset_event}
                    }
                }
            ),
        )

    # https://github.com/opensource-observer/oso/issues/2403
    return AssetFactoryResponse(
        [cast(GenericAsset, gcs_asset)],
        [gcs_clean_up_sensor],
        [gcs_clean_up_job],
    )
