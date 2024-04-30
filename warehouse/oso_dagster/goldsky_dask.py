import time
import asyncio
import duckdb
import copy
import httpx_ws
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, List
from dask.distributed import (
    Client,
    Worker,
    WorkerPlugin,
    get_worker,
    Future as DaskFuture,
)
from concurrent.futures import CancelledError
from dask_kubernetes.operator import KubeCluster, make_cluster_spec
from dagster import DagsterLogManager
from queue import PriorityQueue, Empty
from asyncio import Future as aioFuture


@dataclass(order=True)
class RetryQueueItem:
    priority: int
    type: str = field(compare=False)
    retry_count: int = field(compare=False, default=0)
    operation: Optional[Callable] = field(compare=False, default=None)


class RetryTaskManager:
    client: Client | None
    loop: asyncio.AbstractEventLoop
    cluster: KubeCluster | None
    log: DagsterLogManager
    bucket_key_id: str
    bucket_secret: str
    cluster_spec: dict

    @classmethod
    def setup(
        cls,
        loop: asyncio.AbstractEventLoop,
        bucket_key_id: str,
        bucket_secret: str,
        cluster_spec: dict,
        log: DagsterLogManager,
    ):
        task_manager = cls(
            loop,
            bucket_key_id,
            bucket_secret,
            cluster_spec,
            log,
        )
        task_manager.reconnect()
        return task_manager

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        bucket_key_id: str,
        bucket_secret: str,
        cluster_spec: dict,
        log: DagsterLogManager,
    ):
        self.log = log
        self.loop = loop
        self.bucket_key_id = bucket_key_id
        self.bucket_secret = bucket_secret
        self.cluster_spec = cluster_spec
        self.client = None
        self._reconnection_queued = False
        self.queue = PriorityQueue()
        self._pause_interval = 2500

    def reconnect(self):
        self.log.debug("reconnecting")
        if self.client:
            self.client.close()
            self.cluster.close()

        cluster_spec = copy.deepcopy(self.cluster_spec)
        cluster_spec["metadata"]["name"] = (
            cluster_spec["metadata"]["name"] + f"-{time.time()}"
        )

        self.cluster = KubeCluster(custom_cluster_spec=self.cluster_spec)
        self.cluster.adapt(minimum=8, maximum=50)
        self.client = Client(self.cluster)
        self.client.register_plugin(
            DuckDBGCSPlugin(
                self.bucket_key_id,
                self.bucket_secret,
            ),
            name="duckdb-gcs",
        )
        self.reconnection_time = time.time()
        self._reconnection_queued = False
        self.log.debug("reconnection completed")

    def wrap_future(self, f: DaskFuture):
        loop = self.loop
        aio_future = loop.create_future()

        def on_done(*_):
            try:
                result = f.result()
            except Exception as e:
                loop.call_soon_threadsafe(aio_future.set_exception, e)
            else:
                loop.call_soon_threadsafe(aio_future.set_result, result)

        f.add_done_callback(on_done)
        return aio_future

    def attempt_reconnect(self) -> int:
        now = time.time()
        if now > self._reconnection_time + 120:
            self.reconnect()
            return 0
        else:
            return 0

    def queue_reconnect(self):
        now = time.time()
        if self._reconnection_queued:
            self.reconnection_queued = True
            self.queue.put(RetryQueueItem(priority=1, type="RECONNECT"))
        else:
            return

    def create_retry_future(
        self,
        func,
        args: Any,
        kwargs: Any,
        pure: bool = True,
        retries: int = 3,
        retry_delay: float = 0.5,
    ):
        pass

    def run(self, awaitable: Any):
        self.loop.run_until_complete(self._run(awaitable))

    async def _run(self, awaitable: Any):
        self.loop.create_task(asyncio.to_thread(self.task_loop))
        try:
            await awaitable
        finally:
            self.queue.put(RetryQueueItem(priority=0, type="EXIT"))

    async def task_loop(self):
        """The dask task loop is potentially bad at retrying kubernetes connections

        This task loop processes everything that is supposed to go to
        """
        normal_sleep_time = 0.1
        long_sleep_time = 1
        sleep_time = normal_sleep_time
        submitted = 0
        while True:
            try:
                item: RetryQueueItem = self.queue.get(block=False)
                sleep_time = normal_sleep_time
                if item.type == "EXIT":
                    break
                if item.type == "RECONNECT":
                    self.reconnect()
                    continue
                self.loop.create_task(item.operation(item.retry_count))
                if submitted % self._pause_interval == 0:
                    await asyncio.sleep(10)
                    continue
            except Empty:
                sleep_time += sleep_time
            await asyncio.sleep(sleep_time)

    def new_submit(
        self,
        func,
        args: Any | None = None,
        kwargs: Any | None = None,
        pure: bool = True,
        retries: int = 3,
    ):
        future = self.loop.create_future()

        kwargs = kwargs or {}

        async def run(retry_count: int):
            try:
                result = await self.wrap_future(
                    self.client.submit(func, *args, **kwargs, pure=pure)
                )
                self.log.debug("completed task")
                self.loop.call_soon_threadsafe(future.set_result, result)
                return
            except asyncio.CancelledError as e:
                self.queue_reconnect()
                last_err = e
            except CancelledError as e:
                self.queue_reconnect()
                last_err = e
            except Exception as e:
                last_err = e
            if retry_count > retries:
                self.loop.call_soon_threadsafe(future.set_exception, last_err)
                return
            if retry_count > 1:
                self.log.error(
                    f"Caught an error on a worker. Retrying {last_err} {type(last_err)}"
                )
            self.queue.put(
                RetryQueueItem(
                    priority=100,
                    type="SUBMIT",
                    operation=run,
                    retry_count=retry_count + 1,
                )
            )

        item = RetryQueueItem(
            priority=100,
            type="SUBMIT",
            operation=run,
        )
        self.queue.put(item)
        return future

    async def submit(
        self,
        func,
        args: Any | None = None,
        kwargs: Any | None = None,
        pure: bool = True,
        retries: int = 3,
        retry_delay: float = 0.5,
    ):
        kwargs = kwargs or {}
        # return self.wrap_future(self.client.submit(func, *args, **kwargs, pure=pure))
        retry_count = 0
        last_err = None
        while True:
            try:
                return await self.wrap_future(
                    self.client.submit(func, *args, **kwargs, pure=pure)
                )
            except Exception as e:
                self.log.error(f"Caught an error on a worker. Retrying {e} {type(e)}")
                last_err = e
            if retry_count >= retries:
                if last_err:
                    raise last_err
            retry_count += 1
            await asyncio.sleep(retry_delay)
            retry_delay += retry_delay

    def close(self):
        self.queue.put(RetryQueueItem(priority=0, type="EXIT"))
        if self.client:
            self.client.close()
        if self.cluster:
            self.cluster.close()


async def setup_kube_cluster_client(
    bucket_key_id: str, bucket_secret: str, cluster_spec: dict
):
    cluster = KubeCluster(custom_cluster_spec=cluster_spec)
    cluster.adapt(minimum=8, maximum=50)
    client = Client(cluster)
    client.register_plugin(
        DuckDBGCSPlugin(
            bucket_key_id,
            bucket_secret,
        ),
        name="duckdb-gcs",
    )
    return client


class DuckDBGCSPlugin(WorkerPlugin):
    def __init__(self, key_id: str, secret: str, memory_limit: str = "2GB"):
        self.key_id = key_id
        self.secret = secret
        self.memory_limit = memory_limit
        self._conn = None

    def setup(self, worker: Worker):
        conn = duckdb.connect()
        worker.log_event(
            "info", {"message": "Initializing worker", "key_id": self.key_id}
        )
        conn.sql(
            f"""
        CREATE SECRET (
            TYPE GCS,
            KEY_ID '{self.key_id}',
            SECRET '{self.secret}'
        );
        """
        )
        conn.sql(f"SET memory_limit = '{self.memory_limit}';")
        conn.sql(f"SET enable_progress_bar = false;")
        worker.log_event(
            "info", {"message": "duckdb ready", "memory_limit": self.memory_limit}
        )
        self._conn = conn

    def teardown(self, worker: Worker):
        self.conn.close()

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if not self._conn:
            raise Exception("Duckdb connection not established")
        return self._conn
