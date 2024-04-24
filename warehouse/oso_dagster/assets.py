from concurrent.futures import ProcessPoolExecutor
import os
import uuid
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
    GoldskyDuckDB,
    GoldskyQueueItem,
    GoldskyConfig,
    GoldskyContext,
    GoldskyQueue,
    GoldskyQueues,
    mp_load_goldsky_worker,
)


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


async def load_goldsky_worker(
    job_id: str,
    context: AssetExecutionContext,
    config: GoldskyConfig,
    gs_context: GoldskyContext,
    gs_duckdb: GoldskyDuckDB,
    worker: str,
    queue: GoldskyQueue,
    last_checkpoint_from_previous_run: Optional[int] = None,
):
    context.log.info(f"starting the worker for {worker}")
    item = queue.dequeue()
    if not item:
        context.log.info(f"nothing to load for worker {worker}")
        return
    last_checkpoint = item.checkpoint - 1
    batch_to_load: List[GoldskyQueueItem] = [item]
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

        item = queue.dequeue()
        if not item:
            break
        batch_to_load.append(item)

        if len(batch_to_load) > config.size:
            gs_duckdb.load_and_merge(
                worker,
                current_batch,
                batch_to_load,
            )
            current_batch += 1
            batch_to_load = []
    if len(batch_to_load) > 0:
        gs_duckdb.load_and_merge(
            worker,
            current_batch,
            batch_to_load,
        )
        current_batch += 1
        batch_to_load = []

    # Load all of the tables into bigquery
    with gs_context.bigquery.get_client() as client:
        dest_table_ref = client.get_dataset(config.dataset_name).table(
            f"{config.table_name}_{worker}"
        )
        new = last_checkpoint_from_previous_run is None
        try:
            client.get_table(dest_table_ref)
        except NotFound as exc:
            if last_checkpoint_from_previous_run is not None:
                raise exc
            new = True

        if not new:
            context.log.info("Merging into worker table")
            client.query_and_wait(
                f"""
                LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`
                FROM FILES (
                    format = "PARQUET",
                    uris = ["{gs_duckdb.wildcard_path(worker)}"]
                );
            """
            )
            tx_query = f"""
                BEGIN
                    BEGIN TRANSACTION; 
                        INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}` 
                        SELECT * FROM `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`;

                        INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}_pointer_state` (worker, last_checkpoint)
                        VALUES ('{worker}', {last_checkpoint}); 
                    COMMIT TRANSACTION;
                    EXCEPTION WHEN ERROR THEN
                    -- Roll back the transaction inside the exception handler.
                    SELECT @@error.message;
                    ROLLBACK TRANSACTION;
                END;
            """
            context.log.debug(f"query: {tx_query}")
            client.query_and_wait(tx_query)
            client.query_and_wait(
                f"""
                DROP TABLE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`;
            """
            )
        else:
            context.log.info("Creating new worker table")
            query1 = f"""
                LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}`
                FROM FILES (
                    format = "PARQUET",
                    uris = ["{gs_duckdb.wildcard_path(worker)}"]
                );
            """
            context.log.debug(f"query: {query1}")
            client.query_and_wait(query1)
            rows = client.query_and_wait(
                f"""
                INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}_pointer_state` (worker, last_checkpoint)
                VALUES ('{worker}', {last_checkpoint});
            """
            )
            context.log.info(rows)


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


@asset(key="optimism_traces")
async def testing_goldsky(
    context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
) -> MaterializeResult:
    goldsky_re = re.compile(
        os.path.join("goldsky", "optimism-traces")
        + r"/(?P<job_id>\d+-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-(?P<worker>\d+)-(?P<checkpoint>\d+).parquet"
    )
    gs_config = GoldskyConfig(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "oso_raw_sources",
        "optimism_traces",
        "block_number",
        int(os.environ.get("GOLDSKY_BATCH_SIZE", "40")),
        int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "1000")),
        os.environ.get("DUCKDB_GCS_KEY_ID"),
        os.environ.get("DUCKDB_GCS_SECRET"),
    )

    gcs_client = gcs.get_client()
    blobs = gcs_client.list_blobs("oso-dataset-transfer-bucket", prefix="goldsky")

    parsed_files = []
    gs_job_ids = set()
    queues = GoldskyQueues(max_size=int(os.environ.get("GOLDSKY_MAX_QUEUE_SIZE", 200)))

    worker_status: Mapping[str, int] = {}
    # Get the current state
    with bigquery.get_client() as client:
        try:
            rows = client.query_and_wait(
                f"""
            SELECT worker, MAX(last_checkpoint) AS last_checkpoint
            FROM `{gs_config.project_id}.{gs_config.dataset_name}.{gs_config.table_name}_pointer_state`
            GROUP BY 1;
            """
            )
            for row in rows:
                context.log.debug(row)
                worker_status[row.worker] = row.last_checkpoint
        except NotFound:
            context.log.info("No pointer status found. Will create the table later")

    for blob in blobs:
        match = goldsky_re.match(blob.name)
        if not match:
            context.log.debug(f"skipping {blob.name}")
            continue
        parsed_files.append(match)
        worker = match.group("worker")
        gs_job_ids.add(match.group("job_id"))
        checkpoint = int(match.group("checkpoint"))
        if checkpoint <= worker_status.get(worker, -1):
            context.log.debug(f"skipping {blob.name} as it was already processed")
            continue
        queues.enqueue(
            worker,
            GoldskyQueueItem(
                checkpoint,
                blob.name,
            ),
        )

    if len(gs_job_ids) > 1:
        raise Exception("We aren't currently handling multiple job ids")

    gs_context = GoldskyContext(bigquery, gcs)

    job_id = arrow.now().format("YYYYMMDDHHmm")

    pointer_table = f"{gs_config.project_id}.{gs_config.dataset_name}.{gs_config.table_name}_pointer_state"

    with bigquery.get_client() as client:
        dataset = client.get_dataset(gs_config.dataset_name)
        table_name = f"{gs_config.table_name}_pointer_state"
        pointer_table_ref = dataset.table(table_name)
        try:
            client.get_table(pointer_table_ref)
        except NotFound as exc:
            if table_name in exc.message:
                context.log.info("Pointer table not found.")
                client.query_and_wait(
                    f"""
                CREATE TABLE {pointer_table} (worker STRING, last_checkpoint INT64);
                """
                )
            else:
                raise exc

    # gs_duckdb = GoldskyDuckDB.connect(
    #     f"_temp/{job_id}",
    #     gs_config.bucket_name,
    #     gs_config.bucket_key_id,
    #     gs_config.bucket_secret,
    #     os.environ.get("DAGSTER_DUCKDB_PATH"),
    #     context.log,
    #     os.environ.get("DUCKDB_MEMORY_LIMIT", "16GB"),
    # )

    worker_coroutines = []

    # For each worker
    for worker, queue in queues.worker_queues():
        context.log.info(f"Creating coroutines for worker {worker}")
        await mp_load_goldsky_worker(
            job_id,
            context,
            gs_config,
            gs_context,
            worker,
            queue,
            last_checkpoint_from_previous_run=worker_status.get(worker, None),
        )

    # await asyncio.gather(*worker_coroutines)

    # Create a temporary table to load the current checkpoint

    # Check for duplicates between the current checkpoint and the existing table
    # of data

    # In a transaction
    # -- Merge the dataset into the main table
    # -- Update a source pointer for the current checkpoint (so we don't reprocess)
    # -- Delete the temporary table

    # TODOS
    # Move the data into cold storage

    return MaterializeResult(
        metadata=dict(
            job_id_count=len(gs_job_ids),
            job_ids=list(gs_job_ids),
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


async def sleep_and_print(msg: str, sleep: float):
    await asyncio.sleep(sleep)
    print(msg)


@dataclass
class Boop:
    foo: str
    bar: str


official_name = None


def mp_test(x: Boop, num: int):
    print(f"hi from multiproc {num} {x} {official_name}")


def mp_init(x: int):
    global official_name
    official_name = uuid.uuid4()
    print(f"hi from the multiproc init {x} {official_name}")


@asset
async def async_asset() -> MaterializeResult:
    with ProcessPoolExecutor(8, initializer=mp_init, initargs=(1,)) as executor:
        futures = []
        for i in range(10):
            future = executor.submit(mp_test, Boop("a", "b"), i)
            futures.append(asyncio.wrap_future(future))
        print("wait for the pool to finish")
        await asyncio.gather(*futures)

    return MaterializeResult(metadata={"boop": True})


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
