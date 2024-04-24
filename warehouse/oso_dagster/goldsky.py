import time
import asyncio
from concurrent.futures import ProcessPoolExecutor
from queue import Empty
import multiprocessing as mp
from dataclasses import dataclass
from typing import List, Mapping, Optional
import heapq
import duckdb
from dagster import DagsterLogManager, AssetExecutionContext
from dagster_gcp import BigQueryResource, GCSResource
from google.api_core.exceptions import NotFound


@dataclass
class GoldskyConfig:
    project_id: str
    bucket_name: str
    dataset_name: str
    table_name: str
    partition_column_name: str
    size: int
    pointer_size: int
    bucket_key_id: str
    bucket_secret: str


@dataclass
class GoldskyContext:
    bigquery: BigQueryResource
    gcs: GCSResource


class GoldskyWorkerLoader:
    def __init__(self, worker: str):
        pass


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
            kwargs={"memory_limit": "3GB"},
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
        pass

    def debug(self, *args):
        pass

    def info(self, *args):
        pass


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
        self, worker: str, batch_id: int, blob_name: str, checkpoint: int
    ):
        print("LOADING THE CHECKPOINT------------")
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

        print(query)

        time.sleep(10)
        conn.sql(query)

        print(f"Completed load {blob_name}")


glob_gs_duck: MPGoldskyDuckDB | None = None


def mp_init(destination_path: str, config: GoldskyConfig):
    global glob_gs_duck
    glob_gs_duck = MPGoldskyDuckDB.connect(config, destination_path, "2GB")
    print("initialized a worker!!!!!!!!!!!!!!!")


def mp_run_load(item: MPWorkerItem):
    print("running worker!!!!!!!!!!!!!!!")
    print(f"{item.blob_name}")
    glob_gs_duck.load_and_add_checkpoint(
        item.worker, item.checkpoint, item.blob_name, item.checkpoint
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
    destination_path = (f"_temp/{job_id}",)

    # Create the pool
    with ProcessPoolExecutor(
        8, initializer=mp_init, initargs=(destination_path, config)
    ) as executor:
        futures = []
        context.log.info("Starting the processing pool")
        time.sleep(5)
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
