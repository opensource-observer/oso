import time
import asyncio
import os
import arrow
import re
import json
from dask.distributed import get_worker
from dask_kubernetes.operator import make_cluster_spec
from dataclasses import dataclass
from typing import List, Mapping, Tuple
import heapq
from dagster import asset, AssetExecutionContext
from dagster_gcp import BigQueryResource, GCSResource
from google.api_core.exceptions import NotFound
from google.cloud.bigquery import TableReference
from .goldsky_dask import setup_kube_cluster_client, DuckDBGCSPlugin, RetryTaskManager
from .cbt import CBTResource
from .factories import AssetFactoryResponse


@dataclass(kw_only=True)
class GoldskyConfig:
    # This is the name of the asset within the goldsky directory path in gcs
    project_id: str
    source_name: str
    destination_dataset_name: str
    destination_table_name: str
    pointer_size: int
    bucket_key_id: str
    bucket_secret: str
    max_objects_to_load: int = 200_000
    source_bucket_name: str = "oso-dataset-transfer-bucket"
    destination_bucket_name: str = "oso-dataset-transfer-bucket"
    source_goldsky_dir: str = "goldsky"
    dask_worker_memory: str = "4096Mi"
    dask_scheduler_memory: str = "2560Mi"
    destination_preload_path: str = "_temp"
    dask_image: str = "ghcr.io/opensource-observer/dagster-dask:distributed-test-9"
    dedupe_model: str = "dedupe.sql"
    dedupe_unique_column: str = "id"
    dedupe_order_column: str = "_checkpoint"
    partition_column_name: str = ""


@dataclass
class GoldskyQueueItem:
    checkpoint: int
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


class GoldskyQueues:
    def __init__(self, max_size: int):
        self.queues: Mapping[str, GoldskyQueue] = {}
        self.max_size = max_size

    def enqueue(self, worker: str, item: GoldskyQueueItem):
        queue = self.queues.get(worker, GoldskyQueue(max_size=self.max_size))
        queue.enqueue(item)
        self.queues[worker] = queue

    def dequeue(self, worker: str) -> GoldskyQueueItem | None:
        queue = self.queues.get(worker, GoldskyQueue(max_size=self.max_size))
        return queue.dequeue()

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


def process_goldsky_file(item: GoldskyProcessItem):
    worker = get_worker()
    plugin: DuckDBGCSPlugin = worker.plugins["duckdb-gcs"]
    query = f"""
        COPY (
            SELECT {item.checkpoint} as _checkpoint, *
            FROM read_parquet('{item.source}')
        ) TO '{item.destination}';
    """
    print(f"Querying with: {query}")
    worker.log_event("info", {"message": "running query", "query": query})
    plugin.conn.sql(query)
    return True


class GoldskyWorker:
    def __init__(
        self,
        worker: str,
        job_id: str,
        pointer_table: str,
        latest_checkpoint: int | None,
        gcs: GCSResource,
        bigquery: BigQueryResource,
        config: GoldskyConfig,
        queue: GoldskyQueue,
        task_manager: RetryTaskManager,
    ):
        self.worker = worker
        self.config = config
        self.gcs = gcs
        self.queue = queue
        self.bigquery = bigquery
        self.task_manager = task_manager
        self.job_id = job_id
        self.latest_checkpoint = latest_checkpoint
        self.pointer_table = pointer_table

    def worker_destination_uri(self, filename: str):
        return f"gs://{self.config.source_bucket_name}/{self.worker_destination_path(filename)}"

    def worker_destination_path(self, filename: str):
        return f"{self.config.destination_preload_path}/{self.job_id}/{self.worker}/{filename}"

    @property
    def table(self) -> TableReference:
        with self.bigquery.get_client() as client:
            dest_table_ref = client.get_dataset(
                self.config.destination_dataset_name
            ).table(f"{self.config.destination_table_name}_{self.worker}")
            return dest_table_ref

    @property
    def worker_wildcard_uri(self):
        return self.worker_destination_uri("table_*.parquet")

    async def process(self, context: AssetExecutionContext):
        try:
            await self.process_all_files(context)
        finally:
            await self.clean_preload_files(context)
        return self

    async def process_all_files(self, context: AssetExecutionContext):
        count = 0
        item = self.queue.dequeue()
        current_checkpoint = item.checkpoint
        in_flight = []
        while item is not None:
            source = f"gs://{self.config.source_bucket_name}/{item.blob_name}"
            destination = self.worker_destination_uri(
                f"table_{item.checkpoint}.parquet"
            )
            in_flight.append(
                self.task_manager.submit(
                    process_goldsky_file,
                    args=(
                        GoldskyProcessItem(
                            source=source,
                            destination=destination,
                            checkpoint=item.checkpoint,
                        ),
                    ),
                    pure=False,
                )
            )
            count += 1
            if count >= self.config.pointer_size:
                context.log.debug(
                    f"Worker {self.worker} waiting for {len(in_flight)} blobs to process"
                )
                progress = 0
                for coro in asyncio.as_completed(in_flight):
                    await coro
                    progress += 1
                    context.log.debug(
                        f"Worker[{self.worker}] progress: {progress}/{count}"
                    )
                context.log.debug(f"Worker[{self.worker}] done waiting for blobs")

                # Update the pointer table to the latest item's checkpoint
                await self.update_pointer_table(context, current_checkpoint)

                in_flight = []
                count = 0

            current_checkpoint = item.checkpoint
            item = self.queue.dequeue()

        if len(in_flight) > 0:
            context.log.debug(
                f"Finalizing worker {self.worker} waiting for {len(in_flight)} blobs to process. Last checkpoint {current_checkpoint}",
            )
            progress = 0
            for coro in asyncio.as_completed(in_flight):
                await coro
                progress += 1
                context.log.debug(f"Worker[{self.worker}] progress: {progress}/{count}")
            await self.update_pointer_table(context, current_checkpoint)

        return self.worker

    async def clean_preload_files(self, context: AssetExecutionContext):
        await asyncio.to_thread(
            delete_all_gcs_files_in_prefix,
            context,
            self.gcs,
            self.config.destination_bucket_name,
            self.worker_destination_path(""),
        )

    async def update_pointer_table(
        self, context: AssetExecutionContext, checkpoint: int
    ):
        await asyncio.to_thread(
            blocking_update_pointer_table,
            context,
            self.config,
            self.bigquery,
            self.job_id,
            self.worker,
            self.pointer_table,
            checkpoint,
            self.latest_checkpoint,
            self.worker_wildcard_uri,
        )
        self.latest_checkpoint = checkpoint


def delete_all_gcs_files_in_prefix(
    context: AssetExecutionContext, gcs: GCSResource, bucket_name: str, prefix: str
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


def blocking_update_pointer_table(
    context: AssetExecutionContext,
    config: GoldskyConfig,
    bigquery: BigQueryResource,
    job_id: str,
    worker: str,
    pointer_table: str,
    new_checkpoint: int,
    latest_checkpoint: int | None,
    wildcard_path: str,
):
    with bigquery.get_client() as client:
        dest_table_ref = client.get_dataset(config.destination_dataset_name).table(
            f"{config.destination_table_name}_{worker}"
        )
        new = latest_checkpoint is None
        try:
            client.get_table(dest_table_ref)
        except NotFound as exc:
            if latest_checkpoint is not None:
                raise exc
            new = True

        if not new:
            context.log.info("Merging into worker table")
            client.query_and_wait(
                f"""
                LOAD DATA OVERWRITE `{config.project_id}.{config.destination_dataset_name}.{config.destination_table_name}_{worker}_{job_id}`
                FROM FILES (
                    format = "PARQUET",
                    uris = ["{wildcard_path}"]
                );
            """
            )
            tx_query = f"""
                BEGIN
                    BEGIN TRANSACTION; 
                        INSERT INTO `{config.project_id}.{config.destination_dataset_name}.{config.destination_table_name}_{worker}` 
                        SELECT * FROM `{config.project_id}.{config.destination_dataset_name}.{config.destination_table_name}_{worker}_{job_id}`;

                        INSERT INTO `{pointer_table}` (worker, last_checkpoint)
                        VALUES ('{worker}', {new_checkpoint}); 
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
                DROP TABLE `{config.project_id}.{config.destination_dataset_name}.{config.destination_table_name}_{worker}_{job_id}`;
            """
            )
        else:
            context.log.info("Creating new worker table")
            query1 = f"""
                LOAD DATA OVERWRITE `{config.project_id}.{config.destination_dataset_name}.{config.destination_table_name}_{worker}`
                FROM FILES (
                    format = "PARQUET",
                    uris = ["{wildcard_path}"]
                );
            """
            context.log.debug(f"query: {query1}")
            client.query_and_wait(query1)
            rows = client.query_and_wait(
                f"""
                INSERT INTO `{pointer_table}` (worker, last_checkpoint)
                VALUES ('{worker}', {new_checkpoint});
            """
            )
            context.log.info(rows)


def goldsky_asset(name: str, config: GoldskyConfig) -> AssetFactoryResponse:
    @asset(name=name)
    def generated_asset(
        context: AssetExecutionContext,
        bigquery: BigQueryResource,
        gcs: GCSResource,
        cbt: CBTResource,
    ):
        loop = asyncio.new_event_loop()
        context.log.info(f"Job name?: {context.job_def}")
        gs_asset = GoldskyAsset(gcs, bigquery, cbt, config)
        loop.run_until_complete(gs_asset.materialize(loop, context))

    return AssetFactoryResponse(
        assets=[generated_asset],
    )


class GoldskyAsset:
    def __init__(
        self,
        gcs: GCSResource,
        bigquery: BigQueryResource,
        cbt: CBTResource,
        config: GoldskyConfig,
    ):
        self.config = config
        self.gcs = gcs
        self.bigquery = bigquery
        self.cbt = cbt
        self._task_manager = None
        self._job_id = arrow.now().format("YYYYMMDDHHmm")
        self.cached_blobs_to_process: List[re.Match[str]] | None = None

    async def materialize(
        self, loop: asyncio.AbstractEventLoop, context: AssetExecutionContext
    ):
        context.log.info(
            {"info": "starting goldsky asset load", "name": self.config.source_name}
        )
        workers = await self.load_worker_tables(loop, context)
        # Dedupe and partition the current worker table into a deduped and partitioned table
        await self.dedupe_worker_tables(context, workers)

    async def load_worker_tables(
        self, loop: asyncio.AbstractEventLoop, context: AssetExecutionContext
    ) -> List[GoldskyWorker]:
        context.log.info("loading worker tables for goldsky asset")
        last_restart = time.time()
        retries = 0
        while True:
            try:
                task_manager = RetryTaskManager.setup(
                    loop,
                    self.config.bucket_key_id,
                    self.config.bucket_secret,
                    self.cluster_spec,
                    context.log,
                )
                try:
                    return await self.parallel_load_worker_tables(task_manager, context)
                finally:
                    task_manager.close()
            except Exception as e:
                context.log.error(f"failed?? {e}")
                now = time.time()
                if now > last_restart + 600:
                    last_restart = now
                    retries = 1
                    continue
                else:
                    if retries > 3:
                        raise e
                context.log.error("kube cluster probably disconnected. retrying")
                retries += 1

    async def parallel_load_worker_tables(
        self, task_manager: RetryTaskManager, context: AssetExecutionContext
    ):
        self.ensure_pointer_table(context)

        worker_status, queues = self.load_queues(context)

        context.log.debug(f"spec: ${json.dumps(self.cluster_spec)}")

        job_id = self._job_id

        worker_coroutines = []
        workers: List[GoldskyWorker] = []
        for worker_name, queue in queues.worker_queues():
            worker = GoldskyWorker(
                worker_name,
                job_id,
                self.pointer_table,
                worker_status.get(worker_name, None),
                self.gcs,
                self.bigquery,
                self.config,
                queue,
                task_manager,
            )
            worker_coroutines.append(worker.process(context))
            workers.append(worker)
        for coro in asyncio.as_completed(worker_coroutines):
            worker: GoldskyWorker = await coro
            context.log.info(f"Worker[{worker.worker}] Completed")
        return workers

    async def dedupe_worker_tables(
        self, context: AssetExecutionContext, workers: List[GoldskyWorker]
    ):
        context.log.info("Deduplicating the worker table")
        cbt = self.cbt.get()
        for worker in workers:
            cbt.run_model(
                self.config.dedupe_model,
                worker.table,
                time_partitioning_column=self.config.partition_column_name,
                unique_column=self.config.dedupe_unique_column,
                order_column=self.config.dedupe_order_column,
            )

    def get_worker_status(self, context: AssetExecutionContext):
        worker_status: Mapping[str, int] = {}
        # Get the current state
        with self.bigquery.get_client() as client:
            try:
                rows = client.query_and_wait(
                    f"""
                SELECT worker, MAX(last_checkpoint) AS last_checkpoint
                FROM `{self.pointer_table}`
                GROUP BY 1;
                """
                )
                for row in rows:
                    context.log.debug(row)
                    worker_status[row.worker] = row.last_checkpoint
            except NotFound:
                context.log.info("No pointer status found. Will create the table later")
        return worker_status

    @property
    def pointer_table(self):
        return f"{self.config.project_id}.{self.config.destination_dataset_name}.{self.config.destination_table_name}_pointer_state"

    def ensure_pointer_table(self, context: AssetExecutionContext):
        config = self.config
        pointer_table_name = f"{config.destination_table_name}_pointer_state"
        pointer_table = f"{config.project_id}.{config.destination_dataset_name}.{pointer_table_name}"
        context.log.info(
            f"ensuring that the sync pointer table exists at {pointer_table}"
        )

        with self.bigquery.get_client() as client:
            dataset = client.get_dataset(config.destination_dataset_name)
            pointer_table_ref = dataset.table(pointer_table_name)
            try:
                client.get_table(pointer_table_ref)
            except NotFound as exc:
                if pointer_table_name in exc.message:
                    context.log.info("Pointer table not found.")
                    client.query_and_wait(
                        f"""
                    CREATE TABLE {pointer_table} (worker STRING, last_checkpoint INT64);
                    """
                    )
                else:
                    raise exc

    @property
    def cluster_spec(self):
        spec = make_cluster_spec(
            name=f"{self.config.source_name.replace('_', '-')}-{self._job_id}",
            resources={
                "requests": {"memory": self.config.dask_scheduler_memory},
                "limits": {"memory": self.config.dask_scheduler_memory},
            },
            image=self.config.dask_image,
        )
        spec["spec"]["worker"]["spec"]["tolerations"] = [
            {
                "key": "pool_type",
                "effect": "NoSchedule",
                "operator": "Equal",
                "value": "spot",
            }
        ]
        spec["spec"]["worker"]["spec"]["nodeSelector"] = {"pool_type": "spot"}

        # Give the workers a different resource allocation
        for container in spec["spec"]["worker"]["spec"]["containers"]:
            container["resources"] = {
                "limits": {
                    "memory": self.config.dask_worker_memory,
                },
                "requests": {
                    "memory": self.config.dask_worker_memory,
                },
            }
            if container["name"] == "worker":
                args: List[str] = container["args"]
                args.append("--nthreads")
                args.append("1")
                args.append("--nworkers")
                args.append("1")
                args.append("--memory-limit")
                args.append("0")
        return spec

    @property
    def goldsky_re(self):
        return re.compile(
            os.path.join(self.config.source_goldsky_dir, self.config.source_name)
            + r"/(?P<timestamp>\d+)-(?P<job_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-(?P<worker>\d+)-(?P<checkpoint>\d+).parquet"
        )

    def load_queues(self, context: AssetExecutionContext) -> Tuple[dict, GoldskyQueues]:
        gcs_client = self.gcs.get_client()

        if self.cached_blobs_to_process is None:
            context.log.info("Caching blob list for processing")
            blobs = gcs_client.list_blobs(
                self.config.source_bucket_name,
                prefix=f"{self.config.source_goldsky_dir}/{self.config.source_name}/1714528926",
            )
            self.cached_blobs_to_process = []
            for blob in blobs:
                match = self.goldsky_re.match(blob.name)
                if not match:
                    continue
                self.cached_blobs_to_process.append(match)
        else:
            context.log.info("Using cached blob list for processing")

        gs_job_ids = set()
        examples = dict()
        queues = GoldskyQueues(max_size=self.config.max_objects_to_load)

        # We should not cache the worker status as we may add unnecessary duplicate work
        worker_status = self.get_worker_status(context)

        for match in self.cached_blobs_to_process:
            worker = match.group("worker")
            job_id = match.group("job_id")
            gs_job_ids.add(job_id)
            examples[job_id] = match
            checkpoint = int(match.group("checkpoint"))
            if checkpoint <= worker_status.get(worker, -1):
                continue
            queues.enqueue(
                worker,
                GoldskyQueueItem(
                    checkpoint,
                    match.group(0),
                    match,
                ),
            )

        for worker, queue in queues.worker_queues():
            context.log.debug(f"Worker[{worker}] queue size: {queue.len()}")

        if len(gs_job_ids) > 1:
            context.log.error(examples)
            context.log.error(queues.worker_queues())
            raise Exception("We aren't currently handling multiple job ids")
        return (worker_status, queues)
