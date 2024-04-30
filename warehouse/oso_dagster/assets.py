from concurrent.futures import ProcessPoolExecutor
import os
import uuid
import time
import re
import arrow
import asyncio
import concurrent.futures
from typing import Any, Mapping, List, Optional
from enum import Enum
from pathlib import Path
from google.api_core.exceptions import BadRequest, NotFound
from google.cloud.bigquery.job import CopyJobConfig, QueryJobConfig
from google.cloud.bigquery.table import PartitionRange, RangePartitioning
from google.cloud.bigquery import TableReference
import pandas as pd
from dataclasses import dataclass
from dagster import (
    asset,
    asset_sensor,
    sensor,
    job,
    op,
    SensorDefinition,
    SensorEvaluationContext,
    AssetsDefinition,
    AssetSelection,
    AssetExecutionContext,
    AssetKey,
    JobDefinition,
    MaterializeResult,
    EventLogEntry,
    RunRequest,
    RunConfig,
    OpExecutionContext,
    DefaultSensorStatus,
    DagsterLogManager,
)
from dagster_gcp import BigQueryResource, GCSResource

from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from .constants import main_dbt_manifest_path
from .goldsky import (
    GoldskyConfig,
    GoldskyAsset,
)
from .goldsky_dask import RetryTaskManager


class Interval(Enum):
    Hourly = 0
    Daily = 1
    Weekly = 2
    Monthly = 3


class SourceMode(Enum):
    Incremental = 0
    Overwrite = 1


@dataclass
class BaseGCSAsset:
    project_id: str
    bucket_name: str
    path_base: str
    file_match: str
    destination_table: str
    raw_dataset_name: str
    clean_dataset_name: str


@dataclass
class IntervalGCSAsset(BaseGCSAsset):
    interval: Interval
    mode: SourceMode
    retention_days: int


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        return super().get_asset_key(dbt_resource_props).with_prefix(self._prefix)


@dbt_assets(
    manifest=main_dbt_manifest_path,
    dagster_dbt_translator=CustomDagsterDbtTranslator("main"),
)
def main_dbt_assets(context: AssetExecutionContext, main_dbt: DbtCliResource):
    yield from main_dbt.cli(["build"], context=context).stream()


# @dbt_assets(
#     manifest=source_dbt_manifest_path,
#     dagster_dbt_translator=CustomDagsterDbtTranslator("sources"),
# )
# def source_dbt_assets(context: AssetExecutionContext, source_dbt: DbtCliResource):
#     yield from source_dbt.cli(["build"], context=context).stream()


@asset(key_prefix="sources")
def iris_data(bigquery: BigQueryResource) -> MaterializeResult:
    iris_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    with bigquery.get_client() as client:
        client.create_dataset("oso_raw_sources", exists_ok=True)
        job = client.load_table_from_dataframe(
            dataframe=iris_df,
            destination="oso_raw_sources.test__iris_data",
        )
        job.result()
    return MaterializeResult(
        metadata={
            "num_records": 100,
        }
    )


@dataclass
class AssetFactoryResponse:
    assets: List[AssetsDefinition]
    sensors: List[SensorDefinition]
    jobs: List[JobDefinition]


def parse_interval_prefix(interval: Interval, prefix: str) -> arrow.Arrow:
    return arrow.get(prefix, "YYYYMMDD")


optimism_traces_parallel = GoldskyAsset.setup_asset(
    name="optimism_traces_parallel",
    config=GoldskyConfig(
        "optimism-traces",
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "oso_raw_sources",
        "optimism_traces",
        "block_number",
        int(os.environ.get("GOLDSKY_BATCH_SIZE", "10")),
        int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "100")),
        os.environ.get("DUCKDB_GCS_KEY_ID"),
        os.environ.get("DUCKDB_GCS_SECRET"),
    ),
)

# @asset(key="optimism_traces_parallel")
# def optimism_traces_parallel(
#     context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
# ) -> MaterializeResult:
#     config = GoldskyConfig(
#         "optimism-traces",
#         "opensource-observer",
#         "oso-dataset-transfer-bucket",
#         "oso_raw_sources",
#         "optimism_traces",
#         "block_number",
#         int(os.environ.get("GOLDSKY_BATCH_SIZE", "10")),
#         int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "100")),
#         os.environ.get("DUCKDB_GCS_KEY_ID"),
#         os.environ.get("DUCKDB_GCS_SECRET"),
#     )
#     loop = asyncio.new_event_loop()

#     last_restart = time.time()
#     retries = 0
#     while True:
#         try:
#             asset = GoldskyAsset(gcs, bigquery, config)
#             task_manager = RetryTaskManager.setup(
#                 loop,
#                 config.bucket_key_id,
#                 config.bucket_secret,
#                 asset.cluster_spec,
#                 context.log,
#             )
#             try:
#                 loop.run_until_complete(asset.materialize(task_manager, context))
#                 return
#             finally:
#                 task_manager.close()
#         except Exception as e:
#             now = time.time()
#             if now > last_restart + 120:
#                 last_restart = now
#                 retries = 1
#                 continue
#             else:
#                 if retries > 3:
#                     raise e
#             context.log.error("kube cluster probably disconnected retrying")
#             retries += 1


def interval_gcs_import_asset(key: str, config: IntervalGCSAsset, **kwargs):
    # Find all of the "intervals" in the bucket and load them into the `raw_sources` dataset
    # Run these sources through a secondary dbt model into `clean_sources`

    @asset(key=key, **kwargs)
    def gcs_asset(
        context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
    ) -> MaterializeResult:
        # Check the current state of the bigquery db (we will only load things
        # that are new than that). We continously store the imported data in
        # {project}.{dataset}.{table}_{interval_prefix}.
        with bigquery.get_client() as bq_client:
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
            blobs = client.list_blobs(config.bucket_name, prefix=config.path_base)

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
                format = "CSV",
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

    @op(name=f"{key}_clean_up_op")
    def gcs_clean_up_op(context: OpExecutionContext, config: dict):
        context.log.info(f"Running clean up for {key}")
        print(config)

    @job(name=f"{key}_clean_up_job")
    def gcs_clean_up_job():
        gcs_clean_up_op()

    @asset_sensor(
        asset_key=gcs_asset.key,
        name=f"{key}_clean_up_sensor",
        job=gcs_clean_up_job,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def gcs_clean_up_sensor(
        context: SensorEvaluationContext, gcs: GCSResource, asset_event: EventLogEntry
    ):
        print("EVENT!!!!!!")
        yield RunRequest(
            run_key=context.cursor,
            run_config=RunConfig(
                ops={f"{key}_clean_up_op": {"config": {"asset_event": asset_event}}}
            ),
        )

    return AssetFactoryResponse([gcs_asset], [gcs_clean_up_sensor], [gcs_clean_up_job])


karma3_globaltrust = interval_gcs_import_asset(
    "karma3_globaltrust",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust.csv.gz",
        "karma3__globaltrust",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

karma3_globaltrust_config = interval_gcs_import_asset(
    "karma3_globaltrust_config",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust_config.csv.gz",
        "karma3__globaltrust_config",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

karma3_localtrust = interval_gcs_import_asset(
    "karma3_localtrust",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_localtrust.csv.gz",
        "karma3__localtrust",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)
