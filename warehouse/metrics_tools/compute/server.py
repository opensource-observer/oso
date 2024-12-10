import logging
import typing as t
import uuid
from contextlib import asynccontextmanager

import aiotrino
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from metrics_tools.utils.logging import setup_module_logging

from . import constants
from .cache import (setup_fake_cache_export_manager,
                    setup_trino_cache_export_manager)
from .cluster import (ClusterManager, KubeClusterFactory, LocalClusterFactory,
                      make_new_cluster_with_defaults)
from .service import MetricsCalculationService
from .types import (ClusterStartRequest, EmptyResponse,
                    ExportedTableLoadRequest, QueryJobSubmitRequest)

load_dotenv()
logger = logging.getLogger("uvicorn.error.application")


@asynccontextmanager
async def initialize_app(app: FastAPI):
    # logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    setup_module_logging("metrics_tools")

    logger.setLevel(logging.DEBUG)

    logger.info("Metrics calculation service is starting up")
    if constants.debug_all:
        logger.warning("Debugging all services")

    cache_export_manager = None
    if not constants.debug_cache:
        trino_connection = aiotrino.dbapi.connect(
            host=constants.trino_host,
            port=constants.trino_port,
            user=constants.trino_user,
            catalog=constants.trino_catalog,
        )
        cache_export_manager = await setup_trino_cache_export_manager(
            trino_connection,
            constants.gcs_bucket,
            constants.hive_catalog,
            constants.hive_schema,
            log_override=logger,
        )
    else:
        logger.warning("Loading fake cache export manager")
        cache_export_manager = await setup_fake_cache_export_manager(
            log_override=logger
        )

    cluster_manager = None
    if not constants.debug_cluster:
        cluster_spec = make_new_cluster_with_defaults()
        cluster_factory = KubeClusterFactory(
            constants.cluster_namespace,
            cluster_spec=cluster_spec,
            log_override=logger,
            shutdown_on_close=not constants.debug_cluster_no_shutdown,
        )
        cluster_manager = ClusterManager.with_metrics_plugin(
            constants.gcs_bucket,
            constants.gcs_key_id,
            constants.gcs_secret,
            constants.worker_duckdb_path,
            cluster_factory,
            log_override=logger,
        )
    else:
        logger.warning("Loading fake cluster manager")
        cluster_factory = LocalClusterFactory()
        cluster_manager = ClusterManager.with_dummy_metrics_plugin(
            cluster_factory,
            log_override=logger,
        )

    mcs = MetricsCalculationService.setup(
        id=str(uuid.uuid4()),
        gcs_bucket=constants.gcs_bucket,
        result_path_prefix=constants.results_path_prefix,
        cluster_manager=cluster_manager,
        cache_manager=cache_export_manager,
        log_override=logger,
    )
    try:
        yield {
            "mca": mcs,
        }
    finally:
        await mcs.close()


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
    return await manager.start_cluster(start_request.min_size, start_request.max_size)


@app.post("/cluster/stop")
async def stop_cluster(request: Request):
    """
    Stop the Dask cluster
    """
    state = get_mca(request)
    manager = state.cluster_manager
    return await manager.stop_cluster()


@app.get("/cluster/status")
async def get_cluster_status(request: Request):
    """
    Get the current Dask cluster status
    """
    state = get_mca(request)
    manager = state.cluster_manager
    return await manager.get_cluster_status()


@app.post("/job/submit")
async def submit_job(
    request: Request,
    input: QueryJobSubmitRequest,
):
    """
    Submits a Dask job for calculation
    """
    service = get_mca(request)
    return await service.submit_job(input)


@app.get("/job/status/{job_id}")
async def get_job_status(
    request: Request,
    job_id: str,
):
    """
    Get the status of a job
    """
    include_stats = request.query_params.get("include_stats", "false").lower() == "true"
    service = get_mca(request)
    return await service.get_job_status(job_id, include_stats=include_stats)


@app.post("/cache/manual")
async def add_existing_exported_table_references(
    request: Request, input: ExportedTableLoadRequest
):
    """
    Add a table export to the cache
    """
    service = get_mca(request)
    await service.add_existing_exported_table_references(input.map)
    return EmptyResponse()
