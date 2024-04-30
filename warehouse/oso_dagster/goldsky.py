import time
import asyncio
import os
import arrow
import re
import json
from dask.distributed import (
    Client,
    Worker,
    WorkerPlugin,
    get_worker,
    Future as DaskFuture,
)
from dask_kubernetes.operator import make_cluster_spec
from concurrent.futures import ProcessPoolExecutor, Future
from queue import Empty
import multiprocessing as mp
from dataclasses import dataclass
from typing import List, Mapping, Optional, Any, Tuple
import heapq
import duckdb
from dagster import asset, DagsterLogManager, AssetExecutionContext, MaterializeResult
from dagster_gcp import BigQueryResource, GCSResource
from google.api_core.exceptions import NotFound
from .goldsky_dask import setup_kube_cluster_client, DuckDBGCSPlugin, RetryTaskManager


@dataclass
class GoldskyConfig:
    # This is the name of the asset within the goldsky directory path in gcs
    asset_name: str
    project_id: str
    bucket_name: str
    dataset_name: str
    table_name: str
    partition_column_name: str
    size: int
    pointer_size: int
    bucket_key_id: str
    bucket_secret: str
    worker_memory: str = "4096Mi"
    scheduler_memory: str = "2560Mi"
    goldsky_dir_path: str = "goldsky"
    temp_path: str = "_temp"


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


class GoldskyProcess:
    @classmethod
    def start(
        cls,
        queue: mp.Queue,
        log_queue: mp.Queue,
        gcs_destination_path: str,
        config: GoldskyConfig,
    ):
        proc = mp.Process(
            target=goldsky_process_worker,
            args=(
                gcs_destination_path,
                queue,
                log_queue,
                config,
            ),
            kwargs={
                "memory_limit": os.environ.get("GOLDSKY_PROCESS_DUCKDB_MEMORY", "2GB")
            },
        )
        proc.start()
        return cls(proc, queue)

    def __init__(self, process: mp.Process, queue: mp.Queue):
        self._process = process
        self._queue = queue

    @property
    def process(self):
        return self._process

    @property
    def queue(self):
        return self._queue


class MultiProcessLogger:
    def __init__(self, queue: mp.Queue):
        self.queue = queue

    def debug(self, message: str):
        self.queue.put(["debug", message])

    def info(self, message: str):
        self.queue.put(["info", message])

    def warn(self, message: str):
        self.queue.put(["warn", message])


@dataclass
class MPWorkerItem:
    worker: str
    blob_name: str
    checkpoint: int


def goldsky_process_worker(
    destination_path: str,
    queue: mp.Queue,
    log_queue: mp.Queue,
    config: GoldskyConfig,
    memory_limit: str = "16GB",
):
    gs_duckdb = MPGoldskyDuckDB.connect(
        destination_path,
        config.bucket_name,
        config.bucket_key_id,
        config.bucket_secret,
        "",
        MultiProcessLogger(log_queue),
        memory_limit=memory_limit,
    )

    item: MPWorkerItem = queue.get()
    while True:
        gs_duckdb.load_and_add_checkpoint(
            item.worker, item.checkpoint, item.blob_name, item.checkpoint
        )
        try:
            item = queue.get(block=False)
        except Empty:
            break


class GoldskyDuckDB:
    @classmethod
    def connect(
        cls,
        destination_path: str,
        bucket_name: str,
        key_id: str,
        secret: str,
        path: str,
        log: DagsterLogManager,
        memory_limit: str = "16GB",
    ):
        conn = duckdb.connect()
        conn.sql(
            f"""
        CREATE SECRET (
            TYPE GCS,
            KEY_ID '{key_id}',
            SECRET '{secret}'
        );
        """
        )
        conn.sql(f"SET memory_limit = '{memory_limit}';")
        return cls(bucket_name, destination_path, log, conn)

    def __init__(
        self,
        bucket_name: str,
        destination_path: str,
        log: DagsterLogManager,
        conn: duckdb.DuckDBPyConnection,
    ):
        self.destination_path = destination_path
        self.bucket_name = bucket_name
        self.conn = conn
        self.log = log

    def full_dest_table_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/table_{batch_id}.parquet"

    def full_dest_delete_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/delete_{batch_id}.parquet"

    def full_dest_deduped_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/deduped_{batch_id}.parquet"

    def wildcard_path(self, worker: str):
        return (
            f"gs://{self.bucket_name}/{self.destination_path}/{worker}/table_*.parquet"
        )

    def remove_dupes(self, worker: str, batches: List[int]):
        for batch_id in batches[:-1]:
            self.remove_dupe_for_batch(worker, batch_id)
        self.remove_dupe_for_batch(worker, batches[-1], last=True)

    def remove_dupe_for_batch(self, worker: str, batch_id: int, last: bool = False):
        self.log.info(f"removing duplicates for batch {batch_id}")
        self.conn.sql(
            f"""
        CREATE OR REPLACE TABLE deduped_{worker}_{batch_id}
        AS
        SELECT * FROM read_parquet('{self.full_dest_table_path(worker, batch_id)}')
        """
        )

        if not last:
            self.conn.sql(
                f""" 
            DELETE FROM deduped_{worker}_{batch_id}
            WHERE id in (
                SELECT id FROM read_parquet('{self.full_dest_delete_path(worker, batch_id)}')
            )
            """
            )

        self.conn.sql(
            f"""
        COPY deduped_{worker}_{batch_id} TO '{self.full_dest_deduped_path(worker, batch_id)}';
        """
        )

    def load_and_merge(
        self, worker: str, batch_id: int, batch_items: List[GoldskyQueueItem]
    ):
        conn = self.conn
        bucket_name = self.bucket_name

        base = f"gs://{bucket_name}"

        size = len(batch_items)

        merged_table = f"merged_{worker}_{batch_id}"

        # Start in reverse order and insert into the table
        conn.sql(
            f"""
        CREATE TEMP TABLE {merged_table}
        AS
        SELECT {batch_items[0].checkpoint} AS _checkpoint, *
        FROM read_parquet('{base}/{batch_items[-1].blob_name}')
        """
        )

        for batch_item in batch_items:
            self.log.info(f"Inserting all items in {base}/{batch_item.blob_name}")
            file_ref = f"{base}/{batch_item.blob_name}"
            # TO DO CHECK FOR DUPES IN THE SAME CHECKPOINT
            conn.sql(
                f"""
            INSERT INTO {merged_table}
            SELECT {batch_item.checkpoint} AS _checkpoint, *
            FROM read_parquet('{file_ref}')
            """
            )

        conn.sql(
            f"""
        COPY {merged_table} TO '{self.full_dest_table_path(worker, batch_id)}';
        """
        )

        conn.sql(
            f"""
        DROP TABLE {merged_table};
        """
        )
        self.log.info(f"Completed load and merge {batch_id}")


class MPGoldskyDuckDB:
    @classmethod
    def connect(
        cls,
        config: GoldskyConfig,
        destination_path: str,
        memory_limit: str = "1GB",
    ):
        conn = duckdb.connect()
        conn.sql(
            f"""
        CREATE SECRET (
            TYPE GCS,
            KEY_ID '{config.bucket_key_id}',
            SECRET '{config.bucket_secret}'
        );
        """
        )
        conn.sql(f"SET memory_limit = '{memory_limit}';")
        conn.sql(f"SET enable_progress_bar = false;")
        return cls(config.bucket_name, destination_path, conn)

    def __init__(
        self,
        bucket_name: str,
        destination_path: str,
        conn: duckdb.DuckDBPyConnection,
    ):
        self.destination_path = destination_path
        self.bucket_name = bucket_name
        self.conn = conn

    def full_dest_table_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/table_{batch_id}.parquet"

    def full_dest_delete_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/delete_{batch_id}.parquet"

    def full_dest_deduped_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/deduped_{batch_id}.parquet"

    def wildcard_path(self, worker: str):
        return (
            f"gs://{self.bucket_name}/{self.destination_path}/{worker}/table_*.parquet"
        )

    def load_and_add_checkpoint(
        self,
        worker: str,
        batch_id: int,
        blob_name: str,
        checkpoint: int,
        log: MultiProcessLogger,
    ):
        conn = self.conn
        bucket_name = self.bucket_name

        base = f"gs://{bucket_name}"

        # Start in reverse order and insert into the table
        query = f"""
        COPY (
            SELECT {checkpoint} as _checkpoint, *
            FROM read_parquet('{base}/{blob_name}')
        ) TO '{self.full_dest_table_path(worker, batch_id)}';
        """
        conn.sql(query)

        log.info(f"Completed load {blob_name}")


glob_gs_duck: MPGoldskyDuckDB | None = None
dagster_log: MultiProcessLogger | None = None


def mp_init(log: MultiProcessLogger, config: GoldskyConfig, destination_path: str):
    global glob_gs_duck
    global dagster_log
    dagster_log = log
    glob_gs_duck = MPGoldskyDuckDB.connect(config, destination_path, "2GB")
    log.debug("inititalized worker")


def mp_run_load(item: MPWorkerItem):
    glob_gs_duck.load_and_add_checkpoint(
        item.worker,
        item.checkpoint,
        item.blob_name,
        item.checkpoint,
        dagster_log,
    )


async def mp_load_goldsky_worker(
    job_id: str,
    context: AssetExecutionContext,
    config: GoldskyConfig,
    gs_context: GoldskyContext,
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
    destination_path = f"_temp/{job_id}"
    log_queue = mp.Queue()

    # Create the pool
    with ProcessPoolExecutor(
        int(os.environ.get("GOLDSKY_PROCESS_POOL_SIZE", "10")),
        initializer=mp_init,
        initargs=(
            MultiProcessLogger(log_queue),
            config,
            destination_path,
        ),
    ) as executor:
        futures = []
        context.log.info("Starting the processing pool")
        time.sleep(5)

        async def handle_logs():
            context.log.debug("starting multiproc log handler")
            while True:
                try:
                    log_item = log_queue.get(block=False)
                    if type(log_item) != list:
                        context.log.warn(
                            "received unexpected object in the multiproc logs"
                        )
                        continue
                    else:
                        if log_item[0] == "debug":
                            context.log.debug(log_item[1])
                        if log_item[0] == "info":
                            context.log.info(log_item[1])
                        if log_item[0] == "warn":
                            context.log.warn(log_item[1])

                except Empty:
                    pass
                try:
                    await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    break

        log_task = asyncio.create_task(handle_logs())

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
            future = executor.submit(
                mp_run_load,
                MPWorkerItem(
                    worker=worker,
                    blob_name=item.blob_name,
                    checkpoint=item.checkpoint,
                ),
            )
            context.log.debug(f"wrapping future for {item.blob_name}")
            futures.append(asyncio.wrap_future(future))
        await asyncio.gather(*futures)

        log_task.cancel()

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

        wildcard_path = (
            f"gs://{config.bucket_name}/{destination_path}/{worker}/table_*.parquet"
        )

        if not new:
            context.log.info("Merging into worker table")
            client.query_and_wait(
                f"""
                LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`
                FROM FILES (
                    format = "PARQUET",
                    uris = ["{wildcard_path}"]
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
                    uris = ["{wildcard_path}"]
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

    def worker_destination_path(self, filename: str):
        return f"gs://{self.config.bucket_name}/{self.config.temp_path}/{self.job_id}/{self.worker}/{filename}"

    @property
    def worker_wildcard_path(self):
        return self.worker_destination_path("table_*.parquet")

    async def process(self, context: AssetExecutionContext):
        count = 0
        item = self.queue.dequeue()
        current_checkpoint = item.checkpoint
        in_flight = []
        while item is not None:
            source = f"gs://{self.config.bucket_name}/{item.blob_name}"
            destination = self.worker_destination_path(
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

    def old_update_pointer_table(self, context: AssetExecutionContext, checkpoint: int):
        context.log.debug(f"updating pointer table for {self.worker}")
        config = self.config
        worker = self.worker
        job_id = self.job_id

        with self.bigquery.get_client() as client:
            dest_table_ref = client.get_dataset(config.dataset_name).table(
                f"{config.table_name}_{worker}"
            )
            new = self.latest_checkpoint is None
            try:
                client.get_table(dest_table_ref)
            except NotFound as exc:
                if self.latest_checkpoint is not None:
                    raise exc
                new = True

            wildcard_path = self.worker_wildcard_path

            if not new:
                context.log.info("Merging into worker table")
                client.query_and_wait(
                    f"""
                    LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`
                    FROM FILES (
                        format = "PARQUET",
                        uris = ["{wildcard_path}"]
                    );
                """
                )
                tx_query = f"""
                    BEGIN
                        BEGIN TRANSACTION; 
                            INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}` 
                            SELECT * FROM `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`;

                            INSERT INTO `{self.pointer_table}` (worker, last_checkpoint)
                            VALUES ('{worker}', {checkpoint}); 
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
                        uris = ["{wildcard_path}"]
                    );
                """
                context.log.debug(f"query: {query1}")
                client.query_and_wait(query1)
                rows = client.query_and_wait(
                    f"""
                    INSERT INTO `{self.pointer_table}` (worker, last_checkpoint)
                    VALUES ('{worker}', {checkpoint});
                """
                )
                context.log.info(rows)

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
            self.worker_wildcard_path,
        )
        self.latest_checkpoint = checkpoint


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
        dest_table_ref = client.get_dataset(config.dataset_name).table(
            f"{config.table_name}_{worker}"
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
                LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`
                FROM FILES (
                    format = "PARQUET",
                    uris = ["{wildcard_path}"]
                );
            """
            )
            tx_query = f"""
                BEGIN
                    BEGIN TRANSACTION; 
                        INSERT INTO `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}` 
                        SELECT * FROM `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`;

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
                DROP TABLE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}_{job_id}`;
            """
            )
        else:
            context.log.info("Creating new worker table")
            query1 = f"""
                LOAD DATA OVERWRITE `{config.project_id}.{config.dataset_name}.{config.table_name}_{worker}`
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


class GoldskyAsset:
    @classmethod
    def setup_asset(cls, name: str, config: GoldskyConfig):
        @asset(name=name)
        def goldsky_asset(
            context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
        ):
            loop = asyncio.new_event_loop()
            context.log.info(f"Job name?: {context.job_name}")

            last_restart = time.time()
            retries = 0
            while True:
                try:
                    gs_asset = cls(gcs, bigquery, config)
                    context.log.info(gs_asset.cluster_spec)
                    task_manager = RetryTaskManager.setup(
                        loop,
                        config.bucket_key_id,
                        config.bucket_secret,
                        gs_asset.cluster_spec,
                        context.log,
                    )
                    try:
                        loop.run_until_complete(
                            gs_asset.materialize(task_manager, context)
                        )
                        return
                    finally:
                        task_manager.close()
                except Exception as e:
                    now = time.time()
                    if now > last_restart + 120:
                        last_restart = now
                        retries = 1
                        continue
                    else:
                        if retries > 3:
                            raise e
                    context.log.error("kube cluster probably disconnected retrying")
                    retries += 1

        return goldsky_asset

    def __init__(
        self, gcs: GCSResource, bigquery: BigQueryResource, config: GoldskyConfig
    ):
        self.config = config
        self.gcs = gcs
        self.bigquery = bigquery
        self._task_manager = None
        self._job_id = arrow.now().format("YYYYMMDDHHmm")

    async def materialize(
        self, task_manager: RetryTaskManager, context: AssetExecutionContext
    ):
        context.log.info({"info": "starting goldsky asset", "config": self.config})
        self.ensure_pointer_table(context)

        worker_status, queues = self.load_queues(context)

        context.log.debug(f"spec: ${json.dumps(self.cluster_spec)}")

        # client = await setup_kube_cluster_client(
        #     self.config.bucket_key_id, self.config.bucket_secret, self.cluster_spec
        # )
        job_id = self._job_id

        worker_coroutines = []
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
        for coro in asyncio.as_completed(worker_coroutines):
            worker = await coro
            context.log.info(f"Worker[{worker}] Completed")

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
        return f"{self.config.project_id}.{self.config.dataset_name}.{self.config.table_name}_pointer_state"

    def ensure_pointer_table(self, context: AssetExecutionContext):
        config = self.config
        pointer_table = f"{config.project_id}.{config.dataset_name}.{config.table_name}_pointer_state"

        with self.bigquery.get_client() as client:
            dataset = client.get_dataset(config.dataset_name)
            table_name = f"{config.table_name}_pointer_state"
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

    @property
    def cluster_spec(self):
        spec = make_cluster_spec(
            name=f"{self.config.asset_name.replace('_', '-')}-{self._job_id}",
            resources={
                "requests": {"memory": self.config.scheduler_memory},
                "limits": {"memory": self.config.scheduler_memory},
            },
            image="ghcr.io/opensource-observer/dagster-dask:distributed-test-9",
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
                    "memory": self.config.worker_memory,
                },
                "requests": {
                    "memory": self.config.worker_memory,
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
            os.path.join(self.config.goldsky_dir_path, self.config.asset_name)
            + r"/(?P<job_id>\d+-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-(?P<worker>\d+)-(?P<checkpoint>\d+).parquet"
        )

    def load_queues(self, context: AssetExecutionContext) -> Tuple[dict, GoldskyQueues]:
        gcs_client = self.gcs.get_client()

        blobs = gcs_client.list_blobs("oso-dataset-transfer-bucket", prefix="goldsky")

        parsed_files = []
        gs_job_ids = set()
        queues = GoldskyQueues(
            max_size=int(os.environ.get("GOLDSKY_MAX_QUEUE_SIZE", 10000))
        )

        worker_status = self.get_worker_status(context)

        for blob in blobs:
            match = self.goldsky_re.match(blob.name)
            if not match:
                # context.log.debug(f"skipping {blob.name}")
                continue
            parsed_files.append(match)
            worker = match.group("worker")
            gs_job_ids.add(match.group("job_id"))
            checkpoint = int(match.group("checkpoint"))
            if checkpoint <= worker_status.get(worker, -1):
                # context.log.debug(f"skipping {blob.name} as it was already processed")
                continue
            queues.enqueue(
                worker,
                GoldskyQueueItem(
                    checkpoint,
                    blob.name,
                ),
            )

        for worker, queue in queues.worker_queues():
            context.log.debug(f"Worker[{worker}] queue size: {queue.len()}")

        if len(gs_job_ids) > 1:
            raise Exception("We aren't currently handling multiple job ids")
        return (worker_status, queues)
