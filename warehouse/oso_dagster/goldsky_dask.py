import time
import asyncio
import duckdb
import copy
from dataclasses import dataclass, field
from typing import Any
from dask.distributed import (
    Client,
    Worker,
    WorkerPlugin,
    get_worker,
    Future as DaskFuture,
)
from dask_kubernetes.operator import KubeCluster, make_cluster_spec
from dagster import DagsterLogManager
from concurrent.futures import CancelledError


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
        self._reconnection_time = 0

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
            except CancelledError as e:
                # If this is cancelled treat that as an immediate bail out
                raise e
            except asyncio.CancelledError as e:
                # If this is cancelled treat that as an immediate bail out
                raise e
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
