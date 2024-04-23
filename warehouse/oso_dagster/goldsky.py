from dataclasses import dataclass
from typing import List, Mapping
import heapq
import duckdb
from dagster import DagsterLogManager
from .common import GenericGCSAsset
from dagster_gcp import BigQueryResource, GCSResource


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
