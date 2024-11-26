"""Sets up a dask cluster
"""

import typing as t

from dask.distributed import Client
from dask_kubernetes.operator import KubeCluster, make_cluster_spec

from .worker import MetricsWorkerPlugin


def start_duckdb_cluster(
    namespace: str,
    cluster_spec: t.Optional[dict] = None,
):
    options: t.Dict[str, t.Any] = {"namespace": namespace}
    if cluster_spec:
        options["custom_cluster_spec"] = cluster_spec
    cluster = KubeCluster(**options)
    cluster.adapt(minimum=6, maximum=6)
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
    ):
        self._cluster: t.Optional[KubeCluster] = None
        self._client: t.Optional[Client] = None
        self._cluster_spec = cluster_spec
        self._namespace = namespace
        self._gcs_bucket = gcs_bucket
        self._gcs_key_id = gcs_key_id
        self._gcs_secret = gcs_secret
        self._duckdb_path = duckdb_path

    def start_cluster(self, min_size: int, max_size: int):
        if self._cluster is None:
            # Create a KubeCluster
            self._cluster = start_duckdb_cluster(
                self._namespace,
                self._cluster_spec,
            )
            self._client = Client(self._cluster)
            # Add the custom plugin to the client
            self._client.register_worker_plugin(
                MetricsWorkerPlugin(
                    self._gcs_bucket,
                    self._gcs_key_id,
                    self._gcs_secret,
                    self._duckdb_path,
                )
            )
            return {
                "status": "Cluster started",
                "dashboard_url": self._cluster.dashboard_link,
                "workers": len(self._cluster.scheduler_info["workers"]),
            }
        else:
            # Cluster already exists
            return {
                "status": "Cluster already running",
                "dashboard_url": self._cluster.dashboard_link,
                "workers": len(self._cluster.scheduler_info["workers"]),
            }

    def get_cluster_status(self):
        if self._cluster is None:
            return {"is_ready": False}
        return {
            "is_ready": True,
            "dashboard_url": self._cluster.dashboard_link,
            "workers": len(self._cluster.scheduler_info["workers"]),
        }

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
