"""Sets up a dask cluster
"""

import typing as t
from dask_kubernetes.operator import KubeCluster


def start_duckdb_cluster(
    namespace: str,
    gcs_key_id: str,
    gcs_secret: str,
    duckdb_path: str,
    cluster_spec: t.Optional[dict] = None,
):
    options: t.Dict[str, t.Any] = {"namespace": namespace}
    if cluster_spec:
        options["custom_cluster_spec"] = cluster_spec
    cluster = KubeCluster(**options)
    cluster.adapt(minimum=6, maximum=6)
    return cluster
