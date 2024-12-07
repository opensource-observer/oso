"""Sets up a dask cluster
"""

import logging
import typing as t

from dask.distributed import Client
from dask_kubernetes.operator import KubeCluster, make_cluster_spec
from metrics_tools.compute.types import ClusterStatus

from .worker import MetricsWorkerPlugin
from threading import Thread, Lock

logger = logging.getLogger(__name__)


def start_duckdb_cluster(
    namespace: str,
    cluster_spec: t.Optional[dict] = None,
    min_size: int = 6,
    max_size: int = 6,
):
    options: t.Dict[str, t.Any] = {"namespace": namespace}
    if cluster_spec:
        options["custom_cluster_spec"] = cluster_spec
    cluster = KubeCluster(**options)
    cluster.adapt(minimum=min_size, maximum=max_size)
    return cluster


class ClusterManager:
    """Internal metrics worker cluster manager"""

    def __init__(
        self,
        namespace: str,
        gcs_bucket: str,
        gcs_key_id: str,
        gcs_secret: str,
        duckdb_path: str,
        cluster_spec: t.Optional[dict] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self._cluster: t.Optional[KubeCluster] = None
        self._client: t.Optional[Client] = None
        self._cluster_spec = cluster_spec
        self._namespace = namespace
        self._gcs_bucket = gcs_bucket
        self._gcs_key_id = gcs_key_id
        self._gcs_secret = gcs_secret
        self._duckdb_path = duckdb_path
        self.logger = log_override or logger
        self._starting = False
        self._lock = Lock()
        self._start_thread: t.Optional[Thread] = None

    def start_cluster(self, min_size: int, max_size: int) -> ClusterStatus:
        with self._lock:
            if self._cluster is not None:
                return ClusterStatus(
                    status="Cluster already running",
                    is_ready=True,
                    dashboard_url=self._cluster.dashboard_link,
                    workers=len(self._cluster.scheduler_info["workers"]),
                )
            if self._starting:
                return ClusterStatus(
                    status="Cluster starting",
                    is_ready=False,
                    dashboard_url="",
                    workers=0,
                )
            self._starting = True
            self._start_thread = Thread(
                target=self._start_cluster_internal,
                args=(min_size, max_size),
                daemon=True,
            )
            self._start_thread.start()
            return ClusterStatus(
                status="Cluster starting",
                is_ready=False,
                dashboard_url="",
                workers=0,
            )

    def _start_cluster_internal(self, min_size: int, max_size: int):
        self.logger.info("starting cluster")
        try:
            self._cluster = start_duckdb_cluster(
                self._namespace,
                self._cluster_spec,
                min_size=min_size,
                max_size=max_size,
            )
            self._client = Client(self._cluster)
            self._client.register_worker_plugin(
                MetricsWorkerPlugin(
                    self._gcs_bucket,
                    self._gcs_key_id,
                    self._gcs_secret,
                    self._duckdb_path,
                ),
                name="metrics",
            )
        except Exception as e:
            self.logger.error(f"Failed to start cluster: {e}")
            with self._lock:
                self._starting = False
            raise
        with self._lock:
            self._starting = False

    # def __init__(
    #     self,
    #     namespace: str,
    #     gcs_bucket: str,
    #     gcs_key_id: str,
    #     gcs_secret: str,
    #     duckdb_path: str,
    #     cluster_spec: t.Optional[dict] = None,
    #     log_override: t.Optional[logging.Logger] = None,
    # ):
    #     self._cluster: t.Optional[KubeCluster] = None
    #     self._client: t.Optional[Client] = None
    #     self._cluster_spec = cluster_spec
    #     self._namespace = namespace
    #     self._gcs_bucket = gcs_bucket
    #     self._gcs_key_id = gcs_key_id
    #     self._gcs_secret = gcs_secret
    #     self._duckdb_path = duckdb_path
    #     self.logger = log_override or logger

    # def start_cluster(self, min_size: int, max_size: int) -> ClusterStatus:
    #     self.logger.info("starting cluster")
    #     if self._cluster is None:
    #         # Create a KubeCluster
    #         self._cluster = start_duckdb_cluster(
    #             self._namespace,
    #             self._cluster_spec,
    #             min_size=min_size,
    #             max_size=max_size,
    #         )
    #         self._client = Client(self._cluster)
    #         # Add the custom plugin to the client
    #         self._client.register_worker_plugin(
    #             MetricsWorkerPlugin(
    #                 self._gcs_bucket,
    #                 self._gcs_key_id,
    #                 self._gcs_secret,
    #                 self._duckdb_path,
    #             ),
    #             name="metrics",
    #         )
    #         return ClusterStatus(
    #             status="Cluster started",
    #             is_ready=True,
    #             dashboard_url=self._cluster.dashboard_link,
    #             workers=len(self._cluster.scheduler_info["workers"]),
    #         )
    #     else:
    #         return ClusterStatus(
    #             status="Cluster already running",
    #             is_ready=True,
    #             dashboard_url=self._cluster.dashboard_link,
    #             workers=len(self._cluster.scheduler_info["workers"]),
    #         )

    def stop_cluster(self):
        self.logger.info("stopping cluster")
        if self._cluster is not None:
            self._cluster.close()
            self._cluster = None
            self._client = None

    def get_cluster_status(self):
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
            workers=len(self._cluster.scheduler_info["workers"]),
        )

    @property
    def client(self):
        client = self._client
        assert client is not None, "Client hasn't been initialized"
        return client

    def close(self):
        if self._cluster:
            self._cluster.close()


def make_new_cluster(
    image: str,
    cluster_id: str,
    service_account_name: str,
    threads: int,
    scheduler_memory_request: str,
    scheduler_memory_limit: str,
    worker_memory_request: str,
    worker_memory_limit: str,
):
    spec = make_cluster_spec(
        name=f"{cluster_id}",
        resources={
            "requests": {"memory": scheduler_memory_request},
            "limits": {"memory": scheduler_memory_limit},
        },
        image=image,
    )
    spec["spec"]["scheduler"]["spec"]["tolerations"] = [
        {
            "key": "pool_type",
            "effect": "NoSchedule",
            "operator": "Equal",
            "value": "sqlmesh-worker",
        }
    ]
    spec["spec"]["scheduler"]["spec"]["nodeSelector"] = {"pool_type": "sqlmesh-worker"}

    spec["spec"]["worker"]["spec"]["tolerations"] = [
        {
            "key": "pool_type",
            "effect": "NoSchedule",
            "operator": "Equal",
            "value": "sqlmesh-worker",
        }
    ]
    spec["spec"]["worker"]["spec"]["nodeSelector"] = {"pool_type": "sqlmesh-worker"}

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
