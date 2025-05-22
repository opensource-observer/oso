"""Sets up a dask cluster
"""

import abc
import asyncio
import inspect
import logging
import typing as t

from dask.distributed import Client
from dask.distributed import Future as DaskFuture
from dask.distributed import LocalCluster
from dask_kubernetes.operator import KubeCluster, make_cluster_spec
from metrics_service.types import ClusterConfig, ClusterStatus
from pyee.asyncio import AsyncIOEventEmitter

from .worker import (
    DuckDBMetricsWorkerPlugin,
    DummyMetricsWorkerPlugin,
    MetricsWorkerPlugin,
)

logger = logging.getLogger(__name__)


def start_duckdb_cluster(
    namespace: str,
    cluster_spec: t.Optional[dict] = None,
    min_size: int = 6,
    max_size: int = 6,
    quiet: bool = False,
    **kwargs: t.Any,
):
    options: t.Dict[str, t.Any] = {"namespace": namespace}
    options.update(kwargs)
    print("starting duckdb cluster")
    if cluster_spec:
        options["custom_cluster_spec"] = cluster_spec
    print(cluster_spec)
    print("starting duckdb cluster1")
    cluster = KubeCluster(quiet=quiet, **options)
    print(f"starting duckdb cluster with min_size={min_size} and max_size={max_size}")
    cluster.adapt(minimum=min_size, maximum=max_size)
    return cluster


async def start_duckdb_cluster_async(
    namespace: str,
    resources: t.Dict[str, int],
    cluster_spec: t.Optional[dict] = None,
    min_size: int = 6,
    max_size: int = 6,
    **kwargs: t.Any,
):
    """The async version of start_duckdb_cluster which wraps the sync version in
    a thread. The "async" version of dask's KubeCluster doesn't work as
    expected. So for now we do this."""

    worker_command = ["dask", "worker"]
    resources_to_join = []

    for resource, value in resources.items():
        resources_to_join.append(f"{resource}={value}")
    if resources_to_join:
        resources_str = f'{",".join(resources_to_join)}'
        worker_command.extend(["--resources", resources_str])

    options: t.Dict[str, t.Any] = {"namespace": namespace}
    options.update(kwargs)
    if cluster_spec:
        options["custom_cluster_spec"] = cluster_spec

    # loop = asyncio.get_running_loop()
    cluster = await KubeCluster(asynchronous=True, **options)
    adapt_response = cluster.adapt(minimum=min_size, maximum=max_size)
    if inspect.isawaitable(adapt_response):
        await adapt_response
    return cluster


class ClusterProxy(abc.ABC):
    async def client(self) -> Client:
        raise NotImplementedError("client not implemented")

    async def status(self) -> ClusterStatus:
        raise NotImplementedError("status not implemented")

    async def stop(self):
        raise NotImplementedError("stop not implemented")

    async def adapt(self, minimum: int, maximum: int):
        raise NotImplementedError("adapt not implemented")

    @property
    def dashboard_link(self):
        raise NotImplementedError("dashboard_link not implemented")

    @property
    def workers(self):
        raise NotImplementedError("workers not implemented")


class ClusterFactory(abc.ABC):
    async def create_cluster(self, min_size: int, max_size: int) -> ClusterProxy:
        raise NotImplementedError("start_cluster not implemented")


class LocalClusterProxy(ClusterProxy):
    def __init__(self, cluster: LocalCluster):
        self.cluster = cluster

    async def client(self) -> Client:
        return await Client(self.cluster, asynchronous=True)

    async def status(self) -> ClusterStatus:
        return ClusterStatus(
            status="Cluster running",
            is_ready=True,
            dashboard_url=self.cluster.dashboard_link,
            workers=len(self.cluster.scheduler_info["workers"]),
        )

    async def adapt(self, minimum: int, maximum: int):
        # For local, this is a noop
        return None

    async def stop(self):
        self.cluster.close()

    @property
    def dashboard_link(self):
        return self.cluster.dashboard_link

    @property
    def workers(self):
        return len(self.cluster.scheduler_info["workers"])


class KubeClusterProxy(ClusterProxy):
    def __init__(self, cluster: KubeCluster):
        self.cluster = cluster

    async def client(self) -> Client:
        return await Client(self.cluster, asynchronous=True)

    async def status(self) -> ClusterStatus:
        return ClusterStatus(
            status="Cluster running",
            is_ready=True,
            dashboard_url=self.cluster.dashboard_link,
            workers=len(self.cluster.scheduler_info["workers"]),
        )

    async def adapt(self, minimum: int, maximum: int):
        await self.cluster.adapt(minimum=minimum, maximum=maximum)

    async def stop(self):
        await self.cluster.close()

    @property
    def dashboard_link(self):
        return self.cluster.dashboard_link

    @property
    def workers(self):
        return len(self.cluster.scheduler_info["workers"])


class LocalClusterFactory(ClusterFactory):
    async def create_cluster(self, min_size: int, max_size: int) -> ClusterProxy:
        return LocalClusterProxy(
            await LocalCluster(
                n_workers=max_size, resources={"slots": 10}, asynchronous=True
            )
        )


class KubeClusterFactory(ClusterFactory):
    def __init__(
        self,
        namespace: str,
        resources: t.Dict[str, int],
        cluster_spec: t.Optional[dict] = None,
        log_override: t.Optional[logging.Logger] = None,
        **kwargs: t.Any,
    ):
        self._namespace = namespace
        self.logger = log_override or logger
        self._cluster_spec = cluster_spec
        self._resources = resources
        self.kwargs = kwargs

    async def create_cluster(self, min_size: int, max_size: int):
        cluster = await start_duckdb_cluster_async(
            self._namespace,
            self._resources,
            self._cluster_spec,
            min_size,
            max_size,
            **self.kwargs,
        )
        return KubeClusterProxy(cluster)


class ClusterManager:
    """Internal metrics worker cluster manager"""

    event_emitter: AsyncIOEventEmitter

    @classmethod
    def with_metrics_plugin(
        cls,
        gcs_bucket: str,
        gcs_key_id: str,
        gcs_secret: str,
        duckdb_path: str,
        cluster_factory: ClusterFactory,
        log_override: t.Optional[logging.Logger] = None,
    ):
        def plugin_factory():
            return DuckDBMetricsWorkerPlugin(
                gcs_bucket, gcs_key_id, gcs_secret, duckdb_path
            )

        return cls(plugin_factory, cluster_factory, log_override)

    @classmethod
    def with_dummy_metrics_plugin(
        cls,
        cluster_factory: ClusterFactory,
        log_override: t.Optional[logging.Logger] = None,
    ):
        def plugin_factory():
            return DummyMetricsWorkerPlugin()

        return cls(plugin_factory, cluster_factory, log_override)

    def __init__(
        self,
        plugin_factory: t.Callable[[], MetricsWorkerPlugin],
        cluster_factory: ClusterFactory,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.plugin_factory = plugin_factory
        self._cluster: t.Optional[ClusterProxy] = None
        self._client: t.Optional[Client] = None
        self.logger = log_override or logger
        self._starting = False
        self._lock = asyncio.Lock()
        self.factory = cluster_factory
        self._start_task: t.Optional[asyncio.Task] = None
        self.event_emitter = AsyncIOEventEmitter()

    async def start_cluster(self, min_size: int, max_size: int) -> ClusterStatus:
        async with self._lock:
            if self._cluster is not None:
                self.logger.info("cluster already running")

                # Trigger scaling if necessary

                return ClusterStatus(
                    status="Cluster already running",
                    is_ready=True,
                    dashboard_url=self._cluster.dashboard_link,
                    workers=self._cluster.workers,
                )
            if self._starting:
                self.logger.info("cluster already starting")
                return ClusterStatus(
                    status="Cluster starting",
                    is_ready=False,
                    dashboard_url="",
                    workers=0,
                )
            self.logger.info("cluster not running, starting")
            self._starting = True
            self._start_task = asyncio.create_task(
                self._start_cluster_internal(min_size, max_size)
            )
        return ClusterStatus(
            status="Cluster starting",
            is_ready=False,
            dashboard_url="",
            workers=0,
        )

    async def _start_cluster_internal(self, min_size: int, max_size: int):
        self.logger.info("starting cluster")
        try:
            self.logger.debug("calling create_cluster factory")
            cluster = await self.factory.create_cluster(min_size, max_size)
            self.logger.debug("getting the client")
            client = await cluster.client()
            registration = client.register_worker_plugin(
                self.plugin_factory(),
                name="metrics",
            )
            self.logger.debug(f"What type is {type(registration)}")
            if isinstance(registration, asyncio.Future):
                self.logger.debug("registration is an async future")
                await registration
            if isinstance(registration, DaskFuture):
                self.logger.debug("registration is a dask future")
                await registration
            if isinstance(registration, t.Coroutine):
                self.logger.debug("registration is a coroutine")
                await registration
            self.logger.debug("done registring the client plugin")
            async with self._lock:
                self._cluster = cluster
                self._client = client
        except Exception as e:
            self.logger.error(f"Failed to start cluster: {e}")
            async with self._lock:
                self._starting = False
            raise e
        async with self._lock:
            self._starting = False
        self.logger.debug("emitting cluster_ready")
        self.event_emitter.emit("cluster_ready")

    async def resize_cluster(self, min_size: int, max_size: int):
        async with self._lock:
            if self._cluster is None:
                raise Exception("Cluster not started")
            await self._cluster.adapt(minimum=min_size, maximum=max_size)

    async def stop_cluster(self):
        self.logger.info("stopping cluster")
        async with self._lock:
            if self._cluster is not None:
                await self._cluster.stop()
                self._cluster = None
                self._client = None

    async def get_cluster_status(self):
        async with self._lock:
            if self._cluster is None:
                return ClusterStatus(
                    status="Cluster not started",
                    is_ready=False,
                    dashboard_url="",
                    workers=0,
                )
            return ClusterStatus(
                status="Cluster running",
                is_ready=True,
                dashboard_url=self._cluster.dashboard_link,
                workers=self._cluster.workers,
            )

    @property
    async def client(self):
        self.logger.debug("getting client")
        async with self._lock:
            client = self._client
            assert client is not None, "Client hasn't been initialized"
            return client

    async def close(self):
        if self._start_task and not self._start_task.done():
            await self._start_task

        if self._cluster:
            await self._cluster.stop()

    async def wait_for_ready(self) -> bool:
        async with self._lock:
            if self._cluster is not None:
                self.logger.debug("no wait needed, cluster is ready")
                return True

        future: asyncio.Future[bool] = asyncio.Future()

        def cluster_ready():
            self.logger.info("cluster is ready received")
            future.set_result(True)

        self.event_emitter.once("cluster_ready", cluster_ready)
        return await future


def make_new_cluster(
    *,
    image: str,
    cluster_id: str,
    service_account_name: str,
    threads: int,
    scheduler_memory_request: str,
    scheduler_memory_limit: str,
    scheduler_pool_type: str,
    worker_memory_request: str,
    worker_memory_limit: str,
    worker_pool_type: str,
    worker_resources: t.Dict[str, int],
    worker_command: t.Optional[t.List[str]] = None,
):
    worker_command = worker_command or ["dask", "worker"]
    if worker_resources:
        resources_to_join = []
        for resource, value in worker_resources.items():
            resources_to_join.append(f"{resource}={value}")
        if resources_to_join:
            resources_str = f'{",".join(resources_to_join)}'
            worker_command.extend(["--resources", resources_str])

    spec = make_cluster_spec(
        name=f"{cluster_id}",
        resources={
            "requests": {"memory": scheduler_memory_request},
            "limits": {"memory": scheduler_memory_limit},
        },
        image=image,
        # The type for this says string but it accepts a list
        worker_command=worker_command,  # type: ignore
    )
    spec["spec"]["scheduler"]["spec"]["tolerations"] = [
        {
            "key": "pool_type",
            "effect": "NoSchedule",
            "operator": "Equal",
            "value": scheduler_pool_type,
        }
    ]
    spec["spec"]["scheduler"]["spec"]["nodeSelector"] = {
        "pool_type": scheduler_pool_type
    }

    spec["spec"]["worker"]["spec"]["tolerations"] = [
        {
            "key": "pool_type",
            "effect": "NoSchedule",
            "operator": "Equal",
            "value": worker_pool_type,
        }
    ]
    spec["spec"]["worker"]["spec"]["nodeSelector"] = {"pool_type": worker_pool_type}

    # Give the workers a different resource allocation
    for container in spec["spec"]["worker"]["spec"]["containers"]:
        container["resources"] = {
            "limits": {
                "memory": worker_memory_limit,
            },
            "requests": {
                "memory": worker_memory_request,
            },
        }
        volume_mounts = container.get("volumeMounts", [])
        volume_mounts.append(
            {
                "mountPath": "/scratch",
                "name": "scratch",
            }
        )
        if container["name"] == "worker":
            args: t.List[str] = container["args"]
            args.append("--nthreads")
            args.append(f"{threads}")
            args.append("--nworkers")
            args.append("1")
            args.append("--memory-limit")
            args.append("0")
        container["volumeMounts"] = volume_mounts
    volumes = spec["spec"]["worker"]["spec"].get("volumes", [])
    volumes.append(
        {
            "name": "scratch",
            "emptyDir": {},
        }
    )
    spec["spec"]["worker"]["spec"]["volumes"] = volumes
    spec["spec"]["worker"]["spec"]["serviceAccountName"] = service_account_name

    return spec


def make_new_cluster_with_defaults(config: ClusterConfig):
    # Import here to avoid dependency on constants for all dependents on the
    # cluster module

    return make_new_cluster(
        image=f"{config.cluster_image_repo}:{config.cluster_image_tag}",
        cluster_id=config.cluster_name,
        service_account_name=config.cluster_service_account,
        threads=config.worker_threads,
        scheduler_memory_limit=config.scheduler_memory_limit,
        scheduler_memory_request=config.scheduler_memory_request,
        scheduler_pool_type=config.scheduler_pool_type,
        worker_memory_limit=config.worker_memory_limit,
        worker_memory_request=config.worker_memory_request,
        worker_pool_type=config.worker_pool_type,
        worker_resources=config.worker_resources,
    )
