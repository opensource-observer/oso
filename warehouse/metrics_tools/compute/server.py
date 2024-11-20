import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from dask_kubernetes.operator import make_cluster_spec
from contextlib import asynccontextmanager
from dask.distributed import Client
from .cluster import ClusterManager
import typing as t


application_state: t.Dict[str, t.Any] = {}


@asynccontextmanager
async def cluster_manager():
    cluster_namespace = os.environ.get("METRICS_CLUSTER_NAMESPACE")
    cluster_name = os.environ.get("METRICS_CLUSTER_NAME")

    cluster_spec = make_new_cluster(
        f"ghcr.io/opensource-observer/dagster-dask:{image_tag}",
        cluster_name,
        cluster_namespace,
        threads=threads,
        scheduler_memory_limit=scheduler_memory_limit,
        scheduler_memory_request=scheduler_memory_request,
        worker_memory_limit=worker_memory_limit,
        worker_memory_request=worker_memory_request,
    )
    application_state["cluster_manager"] = ClusterManager(
        os.environ.get("METRICS_K8S_NAMESPACE"),
        os.environ.get("METRICS_GCS_BUCKET"),
        os.environ.get("METRICS_GCS_KEY_ID"),
        os.environ.get("METRICS_GCS_SECRET"),
        os.environ.get("METRICS_DUCKDB_PATH"),
        cluster_spec,
    )
    yield
    del application_state["cluster_manager"]


class QueryInput(BaseModel):
    query_str: str
    start: datetime
    end: datetime
    dialect: str
    batch_size: int
    columns: t.List[t.Tuple[str, str]]
    ref: PeerMetricDependencyRef
    locals: t.Dict[str, t.Any]
    dependent_tables_map: t.Dict[str, str]


# Dependency to get the cluster manager
def get_cluster_manager():
    return cluster_manager


# Dependency to get the Dask client
def get_dask_client(manager: ClusterManager = Depends(get_cluster_manager)) -> Client:
    if manager.client is None:
        raise HTTPException(status_code=400, detail="Cluster is not running")
    return manager.client


app = FastAPI()
cluster_manager = ClusterManager()


class ClusterStartRequest(BaseModel):
    min_size: int
    max_size: int


@app.get("/status")
async def get_status():
    """
    Liveness endpoint
    """
    return {"status": "Service is running"}


@app.post("/cluster/start")
async def start_cluster(
    request: ClusterStartRequest, manager: ClusterManager = Depends(get_cluster_manager)
):
    """
    Start a Dask cluster in an idempotent way
    """
    return manager.start_cluster(request.min_size, request.max_size)


@app.get("/cluster/status")
async def get_cluster_status(manager: ClusterManager = Depends(get_cluster_manager)):
    """
    Get the current Dask cluster status
    """
    return manager.get_cluster_status()


@app.post("/job/submit")
async def submit_job(
    query_input: QueryInput,
    client: Client = Depends(get_dask_client),
):
    """
    Submits a Dask job for calculation
    """
    # Example job submission using query_input
    future = client.submit(
        lambda q: f"Processed query: {q.query_str}", query_input
    )  # Replace with actual query logic
    return {"result": future.result()}
