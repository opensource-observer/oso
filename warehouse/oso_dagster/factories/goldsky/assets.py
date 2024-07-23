import time
import asyncio
import os
import arrow
import re
import io
import random
import threading

import polars
from polars.type_aliases import PolarsDataType
from dataclasses import dataclass
from typing import List, Mapping, Tuple, Dict, Callable, Optional, Any, cast, Unpack
import heapq
from dagster import (
    asset,
    op,
    job,
    asset_sensor,
    AssetsDefinition,
    JobDefinition,
    AssetExecutionContext,
    RunRequest,
    SensorEvaluationContext,
    EventLogEntry,
    RunConfig,
    OpExecutionContext,
    DagsterLogManager,
    DefaultSensorStatus,
    AssetChecksDefinition,
    TableRecord,
    MetadataValue, 
    TableColumn,
    TableSchema
)

from dagster_gcp import BigQueryResource, GCSResource
from google.api_core.exceptions import (
    NotFound,
    InternalServerError,
    ClientError,
)
from google.cloud.bigquery import (
    TableReference,
    LoadJobConfig,
    SourceFormat,
    Client as BQClient,
)
from google.cloud.bigquery.schema import SchemaField
from ...cbt import CBTResource, UpdateStrategy, TimePartitioning
from .. import AssetFactoryResponse
from .config import GoldskyConfig, GoldskyConfigInterface, SchemaDict
from ..common import AssetDeps, AssetList
from ...utils import batch_delete_blobs, add_tags

GenericExecutionContext = AssetExecutionContext | OpExecutionContext

@dataclass
class GoldskyCheckpoint:
    """Orderable representation of the components of the file names for goldsky
    parquet files.

    The file names are in the form: 
    
    * {timestamp}-{job_id}-{worker_number}-{checkpoint}.parquet
    """

    job_id: str
    timestamp: int
    worker_checkpoint: int

    def __lt__(self, other):
        if self.timestamp < other.timestamp:
            return True
        else:
            if self.timestamp != other.timestamp:
                return False
            if self.job_id < other.job_id:
                return True
            else:
                if self.job_id != other.job_id:
                    return False
                return self.worker_checkpoint < other.worker_checkpoint

    def __le__(self, other):
        if self == other:
            return True
        return self < other

    def __eq__(self, other):
        return (
            self.timestamp == other.timestamp
            and self.job_id == other.job_id
            and self.worker_checkpoint == other.worker_checkpoint
        )

    def __gt__(self, other):
        if self == other:
            return False
        return other < self

    def __ge__(self, other):
        if self == other:
            return True
        return self > other


class GoldskyCheckpointRange:
    def __init__(
        self,
        start: Optional[GoldskyCheckpoint] = None,
        end: Optional[GoldskyCheckpoint] = None,
    ):
        self._start = start or GoldskyCheckpoint("0", 0, 0)
        self._end = end

    def in_range(self, checkpoint: GoldskyCheckpoint) -> bool:
        if checkpoint >= self._start:
            if self._end is None:
                return True
            else:
                return checkpoint < self._end
        else:
            return False


@dataclass
class GoldskyQueueItem:
    checkpoint: GoldskyCheckpoint
    blob_name: str
    blob_match: re.Match

    def __lt__(self, other):
        return self.checkpoint < other.checkpoint


class GoldskyQueue:
    def __init__(self, max_size: int):
        self.queue = []
        self._dequeues = 0
        self.max_size = max_size

    def enqueue(self, item: GoldskyQueueItem):
        heapq.heappush(self.queue, item)

    def dequeue(self) -> GoldskyQueueItem | None:
        if self._dequeues > self.max_size - 1:
            return None
        try:
            item = heapq.heappop(self.queue)
            self._dequeues += 1
            return item
        except IndexError:
            return None

    def len(self):
        return len(self.queue)

    def empty(self):
        self.queue = []


class GoldskyQueues:
    def __init__(self, max_size: int):
        self.queues: Dict[str, GoldskyQueue] = {}
        self.max_size = max_size

    def enqueue(self, worker: str, item: GoldskyQueueItem):
        queue = self.queues.get(worker, GoldskyQueue(max_size=self.max_size))
        queue.enqueue(item)
        self.queues[worker] = queue

    def dequeue(self, worker: str) -> GoldskyQueueItem | None:
        queue = self.queues.get(worker, GoldskyQueue(max_size=self.max_size))
        return queue.dequeue()

    def peek(self) -> GoldskyQueueItem | None:
        """Get a value off the top of the queue without popping it"""
        keys = list(self.queues.keys())
        if len(keys) > 0:
            queue = self.queues.get(keys[0])
            if not queue:
                return None
            item = queue.dequeue()
            if not item:
                return None
            queue.enqueue(item)
            return item
        return None

    def empty(self, worker: str):
        queue = self.queues.get(worker, None)
        if queue:
            queue.empty()

    def empty_all(self):
        for _, queue in self.queues.items():
            queue.empty()

    def workers(self):
        return self.queues.keys()

    def status(self):
        status: Mapping[str, int] = {}
        for worker, queue in self.queues.items():
            status[worker] = queue.len()
        return status

    def worker_queues(self):
        return self.queues.items()


@dataclass
class GoldskyProcessItem:
    source: str
    destination: str
    checkpoint: int


class GoldskyWorker:
    def __init__(
        self,
        name: str,
        job_id: str,
        pointer_table: str,
        latest_checkpoint: GoldskyCheckpoint | None,
        gcs: GCSResource,
        bigquery: BigQueryResource,
        config: GoldskyConfig,
        queue: GoldskyQueue,
        schema: List[SchemaField] | None,
    ):
        self.name = name
        self.job_id = job_id
        self.pointer_table = pointer_table
        self.latest_checkpoint = latest_checkpoint
        self.gcs = gcs
        self.bigquery = bigquery
        self.config = config
        self.queue = queue
        self.schema = schema or []

    def worker_destination_uri(self, filename: str):
        return f"gs://{self.config.source_bucket_name}/{self.worker_destination_path(filename)}"

    def worker_destination_path(self, filename: str):
        return f"{self.config.working_destination_preload_path}/{self.job_id}/{self.name}/{filename}"

    @property
    def raw_table(self) -> TableReference:
        with self.bigquery.get_client() as client:
            dest_table_ref = client.get_dataset(
                self.config.working_destination_dataset_name
            ).table(f"{self.config.destination_table_name}_{self.name}")
            return dest_table_ref

    @property
    def deduped_table(self) -> TableReference:
        with self.bigquery.get_client() as client:
            dest_table_ref = client.get_dataset(
                self.config.working_destination_dataset_name
            ).table(f"{self.config.destination_table_name}_deduped_{self.name}")
            return dest_table_ref

    @property
    def worker_wildcard_uri(self):
        return self.worker_destination_uri("table_*.parquet")

    async def process(self, context: GenericExecutionContext, pointer_table_mutex: threading.Lock):
        raise NotImplementedError("process not implemented on the base class")


def bq_retry(
    context: GenericExecutionContext, f: Callable, retries: int = 5, min_wait: float = 1.0
):
    retry_wait = min_wait
    for i in range(retries):
        try:
            return f()
        except InternalServerError:
            context.log.info("Server error encountered. waiting to retry")
            time.sleep(retry_wait)
            retry_wait += min_wait
        except ClientError as e:
            raise e


class DirectGoldskyWorker(GoldskyWorker):
    async def process(
        self,
        context: GenericExecutionContext,
        pointer_table_mutex: threading.Lock,
    ):
        await asyncio.to_thread(
            self.run_load_bigquery_load,
            context,
            pointer_table_mutex,
        )
        return self

    def commit_pointer(
        self,
        context: GenericExecutionContext,
        files_to_load: List[str],
        checkpoint: GoldskyCheckpoint,
        pointer_table_mutex: threading.Lock,
    ):
        with self.bigquery.get_client() as client:
            job_config_options: Dict[str, Any] = dict(
                source_format=SourceFormat.PARQUET,
            )
            if len(self.schema) > 0:
                context.log.debug("schema being overridden")
                job_config_options["schema"] = self.schema
            job_config = LoadJobConfig(**job_config_options)

            def load_retry():
                load_job = client.load_table_from_uri(
                    files_to_load,
                    self.raw_table,
                    job_config=job_config,
                    timeout=self.config.load_table_timeout_seconds,
                )
                return load_job.result()

            bq_retry(context, load_retry)
            context.log.info(f"Worker[{self.name}] Data loaded into bigquery")

            self.update_pointer_table(client, context, checkpoint, pointer_table_mutex)
            context.log.info(
                f"Worker[{self.name}] Pointer table updated to {checkpoint.worker_checkpoint}"
            )

    def run_load_bigquery_load(
        self,
        context: GenericExecutionContext,
        pointer_table_mutex: threading.Lock,
    ):
        to_load: List[str] = []

        item = self.queue.dequeue()
        if not item:
            context.log.info("nothing to load in bigquery")
            return
        latest_checkpoint = item.checkpoint
        while item is not None:
            # For our own convenience we have the option to do a piecemeal
            # loading. However, for direct loading this shouldn't be
            # necessary
            source = f"gs://{self.config.source_bucket_name}/{item.blob_name}"
            to_load.append(source)
            if len(to_load) >= self.config.pointer_size:
                self.commit_pointer(
                    context, to_load, item.checkpoint, pointer_table_mutex
                )
                to_load = []
            latest_checkpoint = item.checkpoint
            item = self.queue.dequeue()

        if len(to_load) > 0:
            self.commit_pointer(
                context, to_load, latest_checkpoint, pointer_table_mutex
            )
            to_load = []

        context.log.debug(f"Worker[{self.name}] all data loaded")

    def update_pointer_table(
        self,
        client: BQClient,
        context: GenericExecutionContext,
        new_checkpoint: GoldskyCheckpoint,
        pointer_table_mutex: threading.Lock,
    ):
        pointer_table = self.pointer_table
        # Only one mutation on the table should be happening at a time
        tx_query = f"""
            BEGIN TRANSACTION; 
                DELETE FROM `{pointer_table}` WHERE worker = '{self.name}';

                INSERT INTO `{pointer_table}` (worker, job_id, timestamp, checkpoint)
                VALUES ('{self.name}', '{new_checkpoint.job_id}', {new_checkpoint.timestamp}, {new_checkpoint.worker_checkpoint}); 
            COMMIT TRANSACTION;
        """
        for i in range(3):
            try:
                with pointer_table_mutex:
                    resp = client.query_and_wait(tx_query)
                context.log.debug(f"TX response: {list(resp)}")
                return resp
            except Exception as e:
                context.log.debug(f"Pointer update failed with `{e}`. Retrying.")
                time.sleep(1 * random.random())
                continue



def delete_all_gcs_files_in_prefix(
    context: GenericExecutionContext, gcs: GCSResource, bucket_name: str, prefix: str
):
    context.log.info(f"deleting files in gs://{bucket_name}/{prefix}")
    client = gcs.get_client()
    try:
        bucket = client.bucket(bucket_name)
        blobs_to_delete = list(client.list_blobs(bucket_name, prefix=prefix))
        bucket.delete_blobs(blobs=blobs_to_delete)
    finally:
        client.close()
    return


def decimal_convert(name: str, field: PolarsDataType):
    field = cast(polars.Decimal, field)
    if field.precision == 100 and field.scale == 0:
        return SchemaField(name, field_type="NUMERIC")
    
    if not field.precision:
        raise Exception("no precision given")

    return SchemaField(
        name, field_type="DECIMAL", precision=field.precision, scale=field.scale
    )


def basic_type_convert(type_name: str):
    def _convert(name: str, _: PolarsDataType):
        return SchemaField(name, field_type=type_name)

    return _convert


def list_type_convert(name: str, field: PolarsDataType):
    field = cast(polars.List, field)
    inner = field.inner
    if not inner:
        raise Exception("no inner type was given")
    inner_type: SchemaField = PARQUET_TO_BQ_FIELD_TYPES[inner]("_inner", inner)
    return SchemaField(name, field_type=inner_type.field_type, mode="REPEATED")


PARQUET_TO_BQ_FIELD_TYPES: Dict[PolarsDataType, Callable[[str, PolarsDataType], SchemaField]] = {
    polars.Boolean: basic_type_convert("BOOLEAN"),
    polars.Int64: basic_type_convert("INT64"),
    polars.Int32: basic_type_convert("INT64"),
    polars.Date: basic_type_convert("DATE"),
    polars.String: basic_type_convert("STRING"),
    polars.Decimal: decimal_convert,
    polars.Datetime: basic_type_convert("TIMESTAMP"),
    polars.Float64: basic_type_convert("FLOAT64"),
    polars.Float32: basic_type_convert("FLOAT64"),
    polars.List: list_type_convert,
}


class GoldskyAsset:
    def __init__(
        self,
        gcs: GCSResource,
        bigquery: BigQueryResource,
        cbt: CBTResource,
        config: GoldskyConfig,
        pointer_table_suffix: str = "",
    ):
        self.config = config
        self.gcs = gcs
        self.bigquery = bigquery
        self.cbt = cbt
        self._task_manager = None
        self._job_id = arrow.now().format("YYYYMMDDHHmm")
        self.cached_blobs_to_process: List[re.Match[str]] | None = None
        self.schema: List[SchemaField] = []
        self.pointer_table_suffix = pointer_table_suffix
        self.bucket_stats = {}
        self.total_files_count = 0

    async def materialize(
        self,
        loop: asyncio.AbstractEventLoop,
        context: GenericExecutionContext,
        checkpoint_range: Optional[GoldskyCheckpointRange] = None,
    ):
        context.log.info(
            {"info": "starting goldsky asset load", "name": self.config.source_name}
        )
        self.ensure_datasets(context)

        workers = await self.load_worker_tables(loop, context, checkpoint_range)

        # Dedupe and partition the current worker table into a deduped and partitioned table
        await self.dedupe_worker_tables(context, workers)

        await self.merge_worker_tables(context, workers)

        await self.clean_working_destination(context, workers)

    def load_schema_from_job_id(self, log: DagsterLogManager, job_id: str, timestamp: int):
        queues = self.load_queues(log, max_objects_to_load=1, checkpoint_range=GoldskyCheckpointRange(
            start=GoldskyCheckpoint(job_id, timestamp, 0),
        ))
        self.load_schema(queues)
        return self.schema

    def load_schema(self, queues: GoldskyQueues):
        item = queues.peek()
        if not item:
            raise Exception("cannot load schema. empty queue")
        client = self.gcs.get_client()
        try:
            # Download the parquet file
            # Load the parquet file to get the schema
            bucket = client.bucket(self.config.source_bucket_name)
            blob = bucket.get_blob(item.blob_name)
            if not blob:
                raise Exception("cannot load schema. failed to get blob")
            blob_as_file = io.BytesIO()
            blob.download_to_file(blob_as_file)
            parquet_schema = polars.read_parquet_schema(blob_as_file)
            schema: List[SchemaField] = []
            overrides_lookup = dict()
            for override in self.config.schema_overrides:
                if isinstance(override, dict):
                    override = cast(SchemaDict, override)
                    overrides_lookup[override["name"]] = SchemaField(**override)
                elif isinstance(override, SchemaField):
                    overrides_lookup[override.name] = override
                else:
                    raise Exception("unexpected input for schema override")
            for field_name, field in parquet_schema.items():
                if field_name in overrides_lookup:
                    schema.append(overrides_lookup[field_name])
                    continue
                field_type_converter = PARQUET_TO_BQ_FIELD_TYPES[type(field)]
                schema_field = field_type_converter(field_name, field)
                schema.append(schema_field)
            self.schema = schema
        finally:
            client.close()

    def ensure_datasets(self, context: GenericExecutionContext):
        self.ensure_dataset(context, self.config.destination_dataset_name)
        self.ensure_dataset(context, self.config.working_destination_dataset_name)

    def ensure_dataset(self, context: GenericExecutionContext, dataset_id: str):
        with self.bigquery.get_client() as client:
            try:
                client.get_dataset(dataset_id)
            except NotFound:
                context.log.info(f"Creating dataset {dataset_id}")
                client.create_dataset(dataset_id)

    async def load_worker_tables(
        self,
        loop: asyncio.AbstractEventLoop,
        context: GenericExecutionContext,
        checkpoint_range: Optional[GoldskyCheckpointRange],
    ):
        self.ensure_pointer_table(context)
        return await self.direct_load_worker_tables(context, checkpoint_range)

    async def direct_load_worker_tables(
        self,
        context: GenericExecutionContext,
        checkpoint_range: Optional[GoldskyCheckpointRange],
    ) -> List[GoldskyWorker]:
        worker_coroutines = []
        workers: List[GoldskyWorker] = []
        worker_status, queues = self.load_queues_to_process(
            context.log, checkpoint_range
        )

        if len(self.config.schema_overrides) > 0:
            self.load_schema(queues)

        pointer_table_mutex = threading.Lock()
        for worker_name, queue in queues.worker_queues():
            worker = DirectGoldskyWorker(
                worker_name,
                self._job_id,
                self.pointer_table,
                worker_status.get(worker_name, None),
                self.gcs,
                self.bigquery,
                self.config,
                queue,
                self.schema,
            )
            worker_coroutines.append(worker.process(context, pointer_table_mutex))
            workers.append(worker)
        for coro in asyncio.as_completed(worker_coroutines):
            worker: GoldskyWorker = await coro
            context.log.info(f"Worker[{worker.name}] completed latest data load")
        return workers

    async def dedupe_worker_tables(
        self, context: GenericExecutionContext, workers: List[GoldskyWorker]
    ):
        cbt = self.cbt.get(context.log)
        coroutines = []
        for worker in workers:
            context.log.info(f"Deduplicating the Worker[{worker.name}] raw table")
            time_partitioning = None
            if self.config.partition_column_name:
                time_partitioning = TimePartitioning(
                    self.config.partition_column_name, self.config.partition_column_type
                )
            coroutines.append(
                asyncio.to_thread(
                    cbt.transform,
                    self.config.dedupe_model,
                    worker.deduped_table,
                    time_partitioning=time_partitioning,
                    unique_column=self.config.dedupe_unique_column,
                    order_column=self.config.dedupe_order_column,
                    partition_column_name=self.config.partition_column_name,
                    partition_column_transform=self.config.partition_column_transform,
                    raw_table=worker.raw_table,
                    timeout=self.config.transform_timeout_seconds,
                )
            )
        completed = 0
        for coro in asyncio.as_completed(coroutines):
            await coro
            completed += 1
            context.log.info(f"Dedupe progress {completed}/{len(coroutines)}")

    async def merge_worker_tables(
        self, context: GenericExecutionContext, workers: List[GoldskyWorker]
    ):
        cbt = self.cbt.get(context.log)

        context.log.info(
            f"Merging all worker tables to final destination: {self.config.destination_table_fqn}"
        )
        time_partitioning = None
        if self.config.partition_column_name:
            time_partitioning = TimePartitioning(
                self.config.partition_column_name, self.config.partition_column_type
            )

        cbt.transform(
            self.config.merge_workers_model,
            self.config.destination_table_fqn,
            update_strategy=UpdateStrategy.MERGE,
            time_partitioning=time_partitioning,
            partition_column_name=self.config.partition_column_name,
            partition_column_transform=self.config.partition_column_transform,
            unique_column=self.config.dedupe_unique_column,
            order_column=self.config.dedupe_order_column,
            workers=workers,
            timeout=self.config.transform_timeout_seconds,
        )

    async def clean_working_destination(
        self, context: GenericExecutionContext, workers: List[GoldskyWorker]
    ):
        # For now we just need to be careful not to run this in multiple processes
        with self.bigquery.get_client() as client:
            for worker in workers:
                context.log.debug(f"deleting Worker[{worker.name}] working tables")
                client.delete_table(worker.raw_table)
                client.delete_table(worker.deduped_table)

    def get_worker_status(self, log: DagsterLogManager):
        worker_status: Mapping[str, GoldskyCheckpoint] = {}
        # Get the current state
        with self.bigquery.get_client() as client:
            try:
                rows = client.query_and_wait(
                    f"""
                SELECT worker, timestamp, job_id, checkpoint
                FROM `{self.pointer_table}`
                """
                )
                for row in rows:
                    worker_status[row.worker] = GoldskyCheckpoint(
                        job_id=row.job_id,
                        timestamp=row.timestamp,
                        worker_checkpoint=row.checkpoint,
                    )
                    log.info(
                        f"Worker[{row.worker}]: Last checkpoint @ TS:{row.timestamp} JOB:{row.job_id} CHK:{row.checkpoint}"
                    )
            except NotFound:
                log.info(
                    f"No pointer status found at {self.pointer_table}. Will create the table later"
                )
        return worker_status

    @property
    def pointer_table(self):
        return f"{self.config.project_id}.{self.config.working_destination_dataset_name}.{self.pointer_table_name}"

    @property
    def pointer_table_name(self):
        pointer_table_suffix = self.pointer_table_suffix
        if pointer_table_suffix != "" and not pointer_table_suffix.startswith("_"):
            pointer_table_suffix = f"_{pointer_table_suffix}"
        return f"{self.config.destination_table_name}_pointer_state{self.pointer_table_suffix}"

    def ensure_pointer_table(self, context: GenericExecutionContext):
        config = self.config
        pointer_table_name = self.pointer_table_name
        pointer_table = self.pointer_table
        context.log.info(
            f"ensuring that the sync pointer table exists at {pointer_table}"
        )

        with self.bigquery.get_client() as client:
            dataset = client.get_dataset(config.working_destination_dataset_name)
            pointer_table_ref = dataset.table(pointer_table_name)
            try:
                client.get_table(pointer_table_ref)
            except NotFound as exc:
                if pointer_table_name in exc.message:
                    context.log.info("Pointer table not found.")
                    client.query_and_wait(
                        f"""
                    CREATE TABLE {pointer_table} (worker STRING, timestamp INT64, job_id STRING, checkpoint INT64);
                    """
                    )
                else:
                    raise exc

    @property
    def goldsky_re(self):
        return re.compile(
            os.path.join(self.config.source_goldsky_dir, self.config.source_name)
            + r"/(?P<timestamp>\d+)-(?P<job_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-(?P<worker>\d+)-(?P<checkpoint>\d+).parquet"
        )

    def clean_up(self, log: DagsterLogManager):
        worker_status = self.get_worker_status(log)

        end_checkpoint = worker_status.get("0")
        for worker, checkpoint in worker_status.items():
            if checkpoint < end_checkpoint:
                end_checkpoint = checkpoint

        queues = self.load_queues(
            log,
            checkpoint_range=GoldskyCheckpointRange(end=end_checkpoint),
            max_objects_to_load=100_000,
            blobs_loader=self._uncached_blobs_loader,
        )

        for worker, queue in queues.worker_queues():
            cleaning_count = queue.len() - self.config.retention_files
            if cleaning_count <= 0:
                log.info(f"Worker[{worker}]: nothing to clean")
            log.info(f"Worker[{worker}]: cleaning {cleaning_count} files")

            blobs: List[str] = []
            for i in range(cleaning_count):
                item = queue.dequeue()
                if item:
                    blobs.append(item.blob_name)
            last_blob = blobs[-1]
            log.info(f"would delete up to {last_blob}")
            gcs_client = self.gcs.get_client()
            batch_delete_blobs(gcs_client, self.config.source_bucket_name, blobs, 1000)

    def gather_stats(self, log: DagsterLogManager):
        self.load_queues_to_process(
            log,
            None
        )
        return {
            "total_files_count": self.total_files_count,
            "bucket_stats": self.bucket_stats
        }

    def _uncached_blobs_loader(self, log: DagsterLogManager):
        log.info("Loading blobs list for processing")
        gcs_client = self.gcs.get_client()
        blobs = gcs_client.list_blobs(
            self.config.source_bucket_name,
            prefix=f"{self.config.source_goldsky_dir}/{self.config.source_name}",
        )
        blobs_to_process = []
        total_files_count = 0
        for blob in blobs:
            match = self.goldsky_re.match(blob.name)
            total_files_count += 1
            if not match:
                continue
            blobs_to_process.append(match)
        self.total_files_count = total_files_count
        return blobs_to_process

    def _cached_blobs_loader(self, log: DagsterLogManager):
        if self.cached_blobs_to_process is None:
            self.cached_blobs_to_process = self._uncached_blobs_loader(log)
        else:
            log.info("using cached blobs")
        return self.cached_blobs_to_process

    def record_bucket_stats_from_match(self, match: re.Match[str]):
        key = f"{match.group("job_id")}-{match.group("timestamp")}"
        if key not in self.bucket_stats:
            self.bucket_stats[key] = dict(
                job_id=match.group("job_id"),
                timestamp=int(match.group("timestamp")), 
                count=1,
                workers=[match.group("worker")],
            )
        else:
            self.bucket_stats[key]["count"] += 1
            worker = match.group("worker")
            if worker not in self.bucket_stats[key]["workers"]:
                self.bucket_stats[key]["workers"].append(worker)


    def load_queues(
        self,
        log: DagsterLogManager,
        worker_status: Optional[Dict[str, GoldskyCheckpoint]] = None,
        max_objects_to_load: Optional[int] = None,
        blobs_loader: Optional[Callable[[DagsterLogManager], List[re.Match[str]]]] = None,
        checkpoint_range: Optional[GoldskyCheckpointRange] = None,
    ) -> GoldskyQueues:
        latest_timestamp = 0
        if not max_objects_to_load:
            max_objects_to_load = self.config.max_objects_to_load
        queues = GoldskyQueues(max_size=max_objects_to_load)

        if not blobs_loader:
            blobs_loader = self._cached_blobs_loader

        # The default filter condition is to skip things that are _before_ the worker
        blobs_to_process = blobs_loader(log)

        if checkpoint_range:
            log.info(
                {
                    "message": "Using a checkpoint range",
                    "end": checkpoint_range._end,
                    "start": checkpoint_range._start,
                }
            )

        for match in blobs_to_process:
            worker = match.group("worker")
            job_id = match.group("job_id")
            timestamp = int(match.group("timestamp"))
            if timestamp > latest_timestamp:
                latest_timestamp = timestamp
            worker_checkpoint = int(match.group("checkpoint"))
            checkpoint = GoldskyCheckpoint(job_id, timestamp, worker_checkpoint)

            self.record_bucket_stats_from_match(match)

            # If there's a checkpoint range only queue checkpoints within that range
            if checkpoint_range:
                if not checkpoint_range.in_range(checkpoint):
                    continue

            # If there's a worker status then queue if the current checkpoint is
            # greater than or equal to it
            if worker_status:
                worker_checkpoint = worker_status.get(
                    worker, GoldskyCheckpoint("", 0, 0)
                )
                if worker_checkpoint >= checkpoint:
                    continue

            # log.debug(f"Queueing {match.group()}")
            queues.enqueue(
                worker,
                GoldskyQueueItem(
                    checkpoint,
                    match.group(0),
                    match,
                ),
            )
        if worker_status:
            keys = list(worker_status.keys())
            if len(keys) > 0:
                expected_timestamp_of_worker_status = worker_status.get(keys[0])

                # This is all debugging code. No need to fail if this does not
                # exist
                if not expected_timestamp_of_worker_status:
                    return queues
                # Originally multiple timestamp values keys was considered an error
                # but it turns out that this is a normal part of the process. This
                # check is just to get a log for when it does change which might be
                # useful for our own tracing/debugging purposes.
                if expected_timestamp_of_worker_status.timestamp != latest_timestamp:
                    log.info(
                        {
                            "message": (
                                "Pipeline timestamp changed."
                                " This is a normal part of the goldsky process."
                                " Continuing to load chronologically"
                            ),
                            "expected": expected_timestamp_of_worker_status,
                            "actual": latest_timestamp,
                        }
                    )
        return queues

    def load_queues_to_process(
        self,
        log: DagsterLogManager,
        checkpoint_range: Optional[GoldskyCheckpointRange],
    ) -> Tuple[dict[str, GoldskyCheckpoint], GoldskyQueues]:
        worker_status = self.get_worker_status(log)

        queues = self.load_queues(
            log, worker_status=worker_status, checkpoint_range=checkpoint_range
        )

        for worker, queue in queues.worker_queues():
            log.info(f"Worker[{worker}] queue size: {queue.len()}")

        return (worker_status, queues)


@dataclass
class GoldskyBackfillOpInput:
    backfill_label: str
    start_checkpoint: Optional[GoldskyCheckpoint]
    end_checkpoint: Optional[GoldskyCheckpoint]


def goldsky_asset(deps: Optional[AssetDeps | AssetList] = None, **kwargs: Unpack[GoldskyConfigInterface]) -> AssetFactoryResponse:
    asset_config = GoldskyConfig(**kwargs)
    def materialize_asset(
        context: OpExecutionContext,
        bigquery: BigQueryResource,
        gcs: GCSResource,
        cbt: CBTResource,
        checkpoint_range: Optional[GoldskyCheckpointRange] = None,
        pointer_table_suffix: str = "",
    ):
        loop = asyncio.new_event_loop()
        gs_asset = GoldskyAsset(
            gcs, bigquery, cbt, asset_config, pointer_table_suffix=pointer_table_suffix
        )
        loop.run_until_complete(
            gs_asset.materialize(loop, context, checkpoint_range=checkpoint_range)
        )

    deps = deps or []
    deps = cast(AssetDeps, deps)

    key_prefix = asset_config.key_prefix

    tags: Dict[str, str] = {
        "opensource.observer/factory": "goldsky",
        "opensource.observer/environment": asset_config.environment,
    }

    if key_prefix:
        group_name = key_prefix if isinstance(key_prefix, str) else "__".join(list(key_prefix))
        tags["opensource.observer/group"] = group_name
        tags["dagster/concurrency_key"] = group_name

    @asset(name=asset_config.name, key_prefix=asset_config.key_prefix, deps=deps, compute_kind="goldsky", tags=add_tags(tags, {
        "opensource.observer/type": "source", 
    }))
    def generated_asset(
        context: AssetExecutionContext,
        bigquery: BigQueryResource,
        gcs: GCSResource,
        cbt: CBTResource,
    ) -> None:
        context.log.info(f"Run ID: {context.run_id} AssetKey: {context.asset_key}")
        materialize_asset(context, bigquery, gcs, cbt)

    related_ops_prefix = "_".join(generated_asset.key.path)

    @op(name=f"{related_ops_prefix}_clean_up_op", tags=add_tags(tags, {
        "opensource.observer/op-type": "clean-up"
    }))
    def goldsky_clean_up_op(
        context: OpExecutionContext,
        bigquery: BigQueryResource,
        gcs: GCSResource,
        cbt: CBTResource,
        config: dict,
    ) -> None:
        print(config)
        gs_asset = GoldskyAsset(gcs, bigquery, cbt, asset_config)
        gs_asset.clean_up(context.log)

    @op(name=f"{related_ops_prefix}_backfill_op", tags=add_tags(tags, {
        "opensource.observer/op-type": "manual-backfill"
    }))
    def goldsky_backfill_op(
        context: OpExecutionContext,
        bigquery: BigQueryResource,
        gcs: GCSResource,
        cbt: CBTResource,
        config: dict,
    ) -> None:
        start_checkpoint = None
        end_checkpoint = None
        if "start" in config:
            start_checkpoint = GoldskyCheckpoint(*config["start"])
        if "end" in config:
            end_checkpoint = GoldskyCheckpoint(*config["end"])
        op_input = GoldskyBackfillOpInput(
            backfill_label=config["backfill_label"],
            start_checkpoint=start_checkpoint,
            end_checkpoint=end_checkpoint,
        )
        context.log.info("Starting a backfill")
        materialize_asset(
            context,
            bigquery,
            gcs,
            cbt,
            checkpoint_range=GoldskyCheckpointRange(
                start=op_input.start_checkpoint, end=op_input.end_checkpoint
            ),
            pointer_table_suffix=op_input.backfill_label,
        )

    @op(name=f"{related_ops_prefix}_files_stats_op", tags=add_tags(tags,{
        "opensource.observer/op-type": "debug"
    }))
    def goldsky_files_stats_op(
        context: OpExecutionContext, 
        bigquery: BigQueryResource, 
        gcs: GCSResource, 
        cbt: CBTResource
    ) -> None:
        table_schema = TableSchema(
            columns=[
                TableColumn(
                    name="timestamp", type="integer", description="The job timestamp"
                ),
                TableColumn(
                    name="job_id", type="string", description="Description of column1"
                ),
                TableColumn(
                    name="worker_count",
                    type="integer",
                    description="Description of column2",
                ),
                TableColumn(
                    name="avg_files_per_worker",
                    type="float",
                    description="Description of column2",
                ),
                TableColumn(
                    name="total_files",
                    type="integer",
                    description="Description of column2",
                ),
            ]
        )
        gs_asset = GoldskyAsset(gcs, bigquery, cbt, asset_config)
        asset_stats = gs_asset.gather_stats(context.log)
        bucket_stats = asset_stats["bucket_stats"]

        records = []
        job_stats = bucket_stats.values()
        job_stats = sorted(job_stats, key=lambda a: a['timestamp'])

        context.log.info(f"Total files in the bucket {asset_stats["total_files_count"]}")

        for _, job_stats in bucket_stats.items():
            worker_count = len(job_stats["workers"])
            records.append(
                TableRecord(dict(
                    job_id=job_stats["job_id"],
                    worker_count=worker_count,
                    timestamp=job_stats["timestamp"],
                    avg_files_per_worker=job_stats["count"]/worker_count,
                    total_files=job_stats["count"],
                ))
            )

        # Create a TableMetadataValue
        table_metadata = MetadataValue.table(records=records, schema=table_schema)

        # Log the metadata
        context.add_output_metadata({"bucket_stats": table_metadata})

    @op(name=f"{related_ops_prefix}_load_schema_op", tags=add_tags(tags, {
        "opensource.observer/op-type": "debug"
    }))
    def goldsky_load_schema_op(
        context: OpExecutionContext, 
        bigquery: BigQueryResource, 
        gcs: GCSResource, 
        cbt: CBTResource,
        config: dict
    ) -> None:
        table_schema = TableSchema(
            columns=[
                TableColumn(
                    name="column_name", type="string", description="The column name"
                ),
                TableColumn(
                    name="column_type", type="string", description="The type"
                ),
            ]
        )
        gs_asset = GoldskyAsset(gcs, bigquery, cbt, asset_config)
        schema: List[SchemaField] = gs_asset.load_schema_from_job_id(context.log, config["job_id"], config["timestamp"])
        records = []
        for field in schema:
            records.append(TableRecord(dict(column_name=field.name, column_type=field.field_type)))

        table_metadata = MetadataValue.table(records=records, schema=table_schema)
        # Log the metadata
        context.add_output_metadata({"schema": table_metadata})


    @job(name=f"{related_ops_prefix}_clean_up_job", tags=tags)
    def goldsky_clean_up_job():
        goldsky_clean_up_op()

    @job(name=f"{related_ops_prefix}_files_stats_job", tags=tags)
    def goldsky_files_stats_job():
        goldsky_files_stats_op()

    @job(name=f"{related_ops_prefix}_load_schema_job", tags=tags)
    def goldsky_load_schema_job():
        goldsky_load_schema_op()

    @job(name=f"{related_ops_prefix}_backfill_job", tags=tags)
    def goldsky_backfill_job():
        goldsky_backfill_op()

    @asset_sensor(
        asset_key=generated_asset.key,
        name=f"{related_ops_prefix}_clean_up_sensor",
        job=goldsky_clean_up_job,
        default_status=DefaultSensorStatus.STOPPED,
    )
    def goldsky_clean_up_sensor(
        context: SensorEvaluationContext, asset_event: EventLogEntry
    ):
        yield RunRequest(
            run_key=context.cursor,
            run_config=RunConfig(
                ops={
                    f"{related_ops_prefix}_clean_up_op": {
                        "config": {"asset_event": asset_event}
                    }
                }
            ),
        )

    checks: List[AssetChecksDefinition] = []
    for check in asset_config.checks:
        checks.extend(check(asset_config, generated_asset))

    additional_assets: List[AssetsDefinition] = []
    for asset_factory in asset_config.additional_assets:
        additional_assets.extend(asset_factory(asset_config, generated_asset))
    
    additional_jobs: List[JobDefinition] = []
    for job_factory in asset_config.additional_jobs:
        additional_jobs.extend(job_factory(asset_config, generated_asset))
        
    return AssetFactoryResponse(
        assets=[generated_asset] + additional_assets,
        sensors=[goldsky_clean_up_sensor],
        jobs=additional_jobs + [goldsky_clean_up_job, goldsky_backfill_job, goldsky_files_stats_job, goldsky_load_schema_job],
        checks=checks,
    )
