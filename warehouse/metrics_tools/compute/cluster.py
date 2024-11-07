"""Sets up a dask cluster
"""

import typing as t
from dask_kubernetes.operator import KubeCluster
from dask.distributed import (
    Client,
    # Future,
)
from .worker import MetricsWorkerPlugin


def start_duckdb_cluster(
    gcs_key_id: str,
    gcs_secret: str,
    duckdb_path: str,
    cluster_spec: t.Optional[dict] = None,
):
    options = {}
    if cluster_spec:
        options["custom_cluster_spec"] = cluster_spec
    cluster = KubeCluster(**options)
    cluster.adapt(minimum=6, maximum=9)
    client = Client(cluster)
    client.register_plugin(
        MetricsWorkerPlugin(
            gcs_key_id,
            gcs_secret,
            duckdb_path,
        ),
        name="duckdb-gcs",
    )
    return client
