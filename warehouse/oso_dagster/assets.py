import os
import re
import arrow
import heapq
import duckdb
from typing import Any, Mapping, List
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
)
from dagster_gcp import BigQueryResource, GCSResource

from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from .constants import main_dbt_manifest_path
from .goldsky import GoldskyDuckDB


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


@op
def what(context: OpExecutionContext):
    context.log.info("hi i'm in the what")


@job
def boop():
    what()


def parse_interval_prefix(interval: Interval, prefix: str) -> arrow.Arrow:
    return arrow.get(prefix, "YYYYMMDD")


class GenericGCSAsset:
    def clean_up(self):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()


class GoldskyAsset(GenericGCSAsset):
    def clean_up(self):
        pass


@dataclass
class GoldskyConfig:
    project_id: str
    bucket_name: str
    dataset_name: str
    table_name: str
    partition_column_name: str
    size: int
    bucket_key_id: str
    bucket_secret: str


@dataclass
class GoldskyContext:
    bigquery: BigQueryResource
    gcs: GCSResource


@dataclass
class GoldskyQueueItem:
    checkpoint: int
    blob_name: str

    def __lt__(self, other):
        return self.checkpoint < other.checkpoint


class GoldskyQueue:
    def __init__(self):
        self.queue = []

    def enqueue(self, item: GoldskyQueueItem):
        heapq.heappush(self.queue, item)

    def dequeue(self) -> GoldskyQueueItem | None:
        try:
            return heapq.heappop(self.queue)
        except IndexError:
            return None

    def len(self):
        return len(self.queue)


class GoldskyQueues:
    def __init__(self):
        self.queues: Mapping[str, GoldskyQueue] = {}

    def enqueue(self, worker: str, item: GoldskyQueueItem):
        queue = self.queues.get(worker, GoldskyQueue())
        queue.enqueue(item)
        self.queues[worker] = queue

    def dequeue(self, worker: str) -> GoldskyQueueItem | None:
        queue = self.queues.get(worker, GoldskyQueue())
        return queue.dequeue()

    def workers(self):
        return self.queues.keys()

    def status(self):
        status: Mapping[str, int] = {}
        for worker, queue in self.queues.items():
            status[worker] = queue.len()
        return status


class GoldskyWorkerLoader:
    def __init__(self, worker: str):
        pass


def load_goldsky_worker(
    job_id: str,
    context: AssetExecutionContext,
    config: GoldskyConfig,
    gs_context: GoldskyContext,
    gs_duckdb: GoldskyDuckDB,
    worker: str,
    queue: GoldskyQueue,
):
    item = queue.dequeue()
    last_checkpoint = item.checkpoint - 1
    batch_to_load: List[str] = []
    batches: List[int] = []
    current_batch = 0
    while item:
        if item.checkpoint > last_checkpoint:
            if item.checkpoint - 1 != last_checkpoint:
                context.log.info(
                    "potentially missing or checkpoints number jumped unexpectedly. not erroring"
                )
        else:
            raise Exception(
                f"Unexpected out of order checkpoints current: {item.checkpoint} last: {last_checkpoint}"
            )
        if item.checkpoint % 10 == 0:
            context.log.info(f"Processing {item.blob_name}")
        last_checkpoint = item.checkpoint

        batch_to_load.append(queue.dequeue())

        if len(batch_to_load) > config.size:
            gs_duckdb.load_and_merge(
                worker,
                current_batch,
                batch_to_load,
            )
            batches.append(current_batch)
            current_batch += 1
            batch_to_load = []
    if len(batch_to_load) > 0:
        gs_duckdb.load_and_merge(
            worker,
            current_batch,
            batch_to_load,
        )
        batches.append(current_batch)
        current_batch += 1
        batch_to_load = []

    # Reprocess each of the batches and delete using the deletion tables
    gs_duckdb.remove_dupes(worker, batches)

    # Load all of the tables into goldsky
    with gs_context.bigquery.get_client() as client:
        client.query_and_wait(
            f"""
            BEGIN
                BEGIN TRANSACTION
                    LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{job_id}`
                    FROM FILES (
                        format = "PARQUET",
                        uris = ["{gs_duckdb.wildcard_deduped_path(worker)}"]
                    );
                    
                    DELETE FROM `{config.project_id}.{config.dataset_name}.{config.table_name}` 
                    WHERE id IN (
                        SELECT id FROM `{config.project_id}.{config.dataset_name}.{config.table_name}_{job_id}`
                    );

                    INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}` 
                    SELECT * FROM `{config.project_id}.{config.dataset_name}.{config.table_name}_{job_id}`;

                    INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}_pointer_state` (worker, latest_checkpoint)
                    VALUES ('{worker}', {last_checkpoint})
                    
                COMMIT TRANSACTION
                EXCEPTION WHEN ERROR THEN
                -- Roll back the transaction inside the exception handler.
                SELECT @@error.message;
                ROLLBACK TRANSACTION;
            END
        """
        )


def goldsky_into_worker_table(
    context: AssetExecutionContext,
    project_id: str,
    bucket_name: str,
    dataset_name: str,
    table_name: str,
    partition_column_name: str,
    bigquery: BigQueryResource,
    worker: str,
    table_ref_to_merge: TableReference,
):
    with bigquery.get_client() as bq_client:
        worker_table_name = f"{table_name}_worker_{worker}_checkpoint_premerge"
        worker_table = f"{project_id}.{dataset_name}.{worker_table_name}"
        try:
            bq_client.get_table(worker_table)
        except NotFound as exc:
            if worker_table_name in exc.message:
                # The table doesn't exist so we need to copy
                job = bq_client.query(
                    f"""
                SELECT * 
                FROM `{table_ref_to_merge.project}`.`{table_ref_to_merge.dataset_id}`.`{table_ref_to_merge.table_id}`
                """,
                    job_config=QueryJobConfig(
                        range_partitioning=RangePartitioning(
                            PartitionRange(
                                0,
                                1_200_000_000,
                                250_000,
                            )
                        )
                    ),
                )
                pass
            else:
                raise exc


def load_goldsky_queue_item(
    context: AssetExecutionContext,
    project_id: str,
    bucket_name: str,
    dataset_name: str,
    table_name: str,
    partition_column_name: str,
    bigquery: BigQueryResource,
    worker: str,
    item: GoldskyQueueItem,
):
    with bigquery.get_client() as bq_client:
        dataset = bq_client.dataset(project_id)
        temp_table_name = f"{project_id}.{dataset_name}.{table_name}_worker_{worker}_checkpoint_premerge"

        bq_client.query_and_wait(
            f"""
        LOAD DATA OVERWRITE `{temp_table_name}`
        FROM FILES (
            format = "PARQUET",
            uris = ["gs://{bucket_name}/{item.blob_name}"]
        );
        """
        )


@asset
def testing_goldsky(
    context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
) -> MaterializeResult:
    goldsky_re = re.compile(
        os.path.join("goldsky", "optimism-traces")
        + r"/(?P<job_id>\d+-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-(?P<worker>\d+)-(?P<checkpoint>\d+).parquet"
    )

    gcs_client = gcs.get_client()
    blobs = gcs_client.list_blobs("oso-dataset-transfer-bucket", prefix="goldsky")

    parsed_files = []
    job_ids = set()
    queues = GoldskyQueues()
    for blob in blobs:
        match = goldsky_re.match(blob.name)
        if not match:
            context.log.debug(f"skipping {blob.name}")
            continue
        parsed_files.append(match)
        worker = match.group("worker")
        job_ids.add(match.group("job_id"))
        checkpoint = int(match.group("checkpoint"))
        queues.enqueue(
            worker,
            GoldskyQueueItem(
                checkpoint,
                blob.name,
            ),
        )

    # For each worker

    # Create a temporary table to load the current checkpoint

    # Check for duplicates between the current checkpoint and the existing table
    # of data

    # In a transaction
    # -- Merge the dataset into the main table
    # -- Update a source pointer for the current checkpoint (so we don't reprocess)
    # -- Delete the temporary table

    # TODOS
    # Move the data into cold storage

    item = queues.dequeue("0")
    last_checkpoint = item.checkpoint - 1
    while item:
        if item.checkpoint > last_checkpoint:
            if item.checkpoint - 1 != last_checkpoint:
                context.log.info("Missing or checkpoints number jumped")
        else:
            raise Exception(
                f"Unexpected out of order checkpoints current: {item.checkpoint} last: {last_checkpoint}"
            )
        if item.checkpoint % 10 == 0:
            context.log.info(f"Processing {item.blob_name}")
        last_checkpoint = item.checkpoint
        item = queues.dequeue("0")

    if len(job_ids) > 1:
        raise Exception("We aren't currently handling multiple job ids")

    return MaterializeResult(
        metadata=dict(
            job_id_count=len(job_ids),
            job_ids=list(job_ids),
            worker_count=len(queues.workers()),
            workers=list(queues.workers()),
            status=queues.status(),
        )
    )


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
