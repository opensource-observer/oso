import logging
import typing as t
import sys
import uuid
from contextlib import asynccontextmanager

import trino
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from ..utils import env
from .types import ClusterStartRequest, ExportedTableLoad, QueryJobSubmitRequest
from .service import MetricsCalculationService
from .cache import TrinoCacheExportManager
from .cluster import ClusterManager, make_new_cluster

load_dotenv()
logger = logging.getLogger("uvicorn.error.application")

# StreamHandler for the console


@asynccontextmanager
async def initialize_app(app: FastAPI):
    # logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

    logger.info("API is starting up")
    logger.debug("HELLO")
    cluster_namespace = env.required_str("METRICS_CLUSTER_NAMESPACE")
    cluster_name = env.required_str("METRICS_CLUSTER_NAME")
    threads = env.required_int("METRICS_CLUSTER_WORKER_THREADS", 16)
    image_repo = env.required_str(
        "METRICS_CLUSTER_WORKER_IMAGE_REPO", "ghcr.io/opensource-observer/dagster-dask"
    )
    image_tag = env.required_str("METRICS_CLUSTER_WORKER_IMAGE_TAG")
    gcs_bucket = env.required_str("METRICS_GCS_BUCKET")
    gcs_key_id = env.required_str("METRICS_GCS_KEY_ID")
    gcs_secret = env.required_str("METRICS_GCS_SECRET")
    results_path_prefix = env.required_str(
        "METRICS_GCS_RESULTS_PATH_PREFIX", "metrics-calc-service-results"
    )
    duckdb_path = env.required_str("METRICS_DUCKDB_PATH")
    scheduler_memory_limit = env.required_str(
        "METRICS_SCHEDULER_MEMORY_LIMIT", "90000Mi"
    )
    scheduler_memory_request = env.required_str(
        "METRICS_SCHEDULER_MEMORY_REQUEST", "85000Mi"
    )
    worker_memory_limit = env.required_str("METRICS_WORKER_MEMORY_LIMIT", "90000Mi")
    worker_memory_request = env.required_str("METRICS_WORKER_MEMORY_REQUEST", "85000Mi")

    trino_host = env.required_str("METRICS_TRINO_HOST")
    trino_port = env.required_str("METRICS_TRINO_PORT")
    trino_user = env.required_str("METRICS_TRINO_USER")
    trino_catalog = env.required_str("METRICS_TRINO_CATALOG")

    trino_connection = trino.dbapi.connect(
        host=trino_host,
        port=trino_port,
        user=trino_user,
        catalog=trino_catalog,
    )

    cluster_spec = make_new_cluster(
        f"{image_repo}:{image_tag}",
        cluster_name,
        cluster_namespace,
        threads=threads,
        scheduler_memory_limit=scheduler_memory_limit,
        scheduler_memory_request=scheduler_memory_request,
        worker_memory_limit=worker_memory_limit,
        worker_memory_request=worker_memory_request,
    )
    cluster_manager = ClusterManager(
        cluster_namespace,
        gcs_bucket,
        gcs_key_id,
        gcs_secret,
        duckdb_path,
        cluster_spec,
    )
    mcs = MetricsCalculationService.setup(
        id=str(uuid.uuid4()),
        gcs_bucket=gcs_bucket,
        result_path_prefix=results_path_prefix,
        cluster_manager=cluster_manager,
        cache_manager=TrinoCacheExportManager(trino_connection, gcs_bucket),
        log_override=logger,
    )
    yield {
        "mca": mcs,
    }
    mcs.close()


# Dependency to get the cluster manager
def get_mca(request: Request) -> MetricsCalculationService:
    mca = request.state.mca
    assert mca is not None
    return t.cast(MetricsCalculationService, mca)


app = FastAPI(lifespan=initialize_app)


@app.get("/status")
async def get_status():
    """
    Liveness endpoint
    """
    return {"status": "Service is running"}


@app.post("/cluster/start")
async def start_cluster(
    request: Request,
    start_request: ClusterStartRequest,
):
    """
    Start a Dask cluster in an idempotent way
    """
    state = get_mca(request)
    manager = state.cluster_manager
    return manager.start_cluster(start_request.min_size, start_request.max_size)


@app.post("/cluster/stop")
async def stop_cluster(request: Request):
    """
    Stop the Dask cluster
    """
    state = get_mca(request)
    manager = state.cluster_manager
    return manager.stop_cluster()


@app.get("/cluster/status")
async def get_cluster_status(request: Request):
    """
    Get the current Dask cluster status
    """
    state = get_mca(request)
    manager = state.cluster_manager
    return manager.get_cluster_status()


@app.post("/job/submit")
async def submit_job(
    request: Request,
    input: QueryJobSubmitRequest,
):
    """
    Submits a Dask job for calculation
    """
    service = get_mca(request)
    res = service.submit_job(input)
    return res.model_dump()


@app.get("/job/status/{job_id}")
async def get_job_status(
    request: Request,
    job_id: str,
):
    """
    Get the status of a job
    """
    service = get_mca(request)
    return service.get_job_status(job_id)


@app.post("/cache/manual")
async def add_existing_exported_table_references(
    request: Request, input: ExportedTableLoad
):
    """
    Add a table export to the cache
    """
    service = get_mca(request)
    return service.add_existing_exported_table_references(input.map)
