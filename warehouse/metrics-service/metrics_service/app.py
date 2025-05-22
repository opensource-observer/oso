"""The main definition of the metrics calculation service FastAPI application.

Please note, this only defines an app factory that returns an app. If you're
looking for the main entrypoint go to server.py
"""

import asyncio
import logging
import shutil
import tempfile
import typing as t
import uuid
from contextlib import asynccontextmanager

import aiotrino
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.datastructures import State
from fastapi.websockets import WebSocketState
from metrics_service.result import (
    DummyImportAdapter,
    FakeLocalImportAdapter,
    TrinoImportAdapter,
)
from uvicorn.protocols.utils import ClientDisconnected

from .cache import setup_fake_cache_export_manager, setup_trino_cache_export_manager
from .cluster import (
    ClusterManager,
    KubeClusterFactory,
    LocalClusterFactory,
    make_new_cluster_with_defaults,
)
from .service import MetricsCalculationService
from .types import (
    AppConfig,
    AppLifespanFactory,
    ClusterStartRequest,
    EmptyResponse,
    ExportedTableLoadRequest,
    JobStatusResponse,
    JobSubmitRequest,
    PingResponse,
    QueryJobStatus,
)

load_dotenv()
logger = logging.getLogger(__name__)


def default_lifecycle(config: AppConfig):
    @asynccontextmanager
    async def initialize_app(app: FastAPI):
        logger.info("Metrics calculation service is starting up")
        if config.debug_all:
            logger.warning("Debugging all services")

        cache_export_manager = None
        temp_dir = None

        if config.debug_with_duckdb:
            temp_dir = tempfile.mkdtemp()
            logger.debug(f"Created temp dir {temp_dir}")
        if not config.debug_cache:
            trino_connection = aiotrino.dbapi.connect(
                host=config.trino_host,
                port=config.trino_port,
                user=config.trino_user,
                catalog=config.trino_catalog,
            )
            cache_export_manager = await setup_trino_cache_export_manager(
                trino_connection,
                config.gcs_bucket,
                config.hive_catalog,
                config.hive_schema,
            )
            import_adapter = TrinoImportAdapter(
                db=trino_connection,
                gcs_bucket=config.gcs_bucket,
                hive_catalog=config.hive_catalog,
                hive_schema=config.hive_schema,
            )
        else:
            if config.debug_with_duckdb:
                assert temp_dir is not None
                logger.warning("Loading fake cache export manager with duckdb")
                import_adapter = FakeLocalImportAdapter(temp_dir)
            else:
                logger.warning("Loading dummy cache export manager (writes nothing)")
                import_adapter = DummyImportAdapter()
            cache_export_manager = await setup_fake_cache_export_manager()

        cluster_manager = None
        if not config.debug_cluster:
            cluster_spec = make_new_cluster_with_defaults(config)
            cluster_factory = KubeClusterFactory(
                config.cluster_namespace,
                config.worker_resources,
                cluster_spec=cluster_spec,
                shutdown_on_close=not config.debug_cluster_no_shutdown,
            )
            cluster_manager = ClusterManager.with_metrics_plugin(
                config.gcs_bucket,
                config.gcs_key_id,
                config.gcs_secret,
                config.worker_duckdb_path,
                cluster_factory,
            )
        else:
            logger.warning("Loading fake cluster manager")
            cluster_factory = LocalClusterFactory()
            cluster_manager = ClusterManager.with_dummy_metrics_plugin(
                cluster_factory,
            )

        mcs = MetricsCalculationService.setup(
            id=str(uuid.uuid4()),
            gcs_bucket=config.gcs_bucket,
            result_path_prefix=config.results_path_prefix,
            cluster_manager=cluster_manager,
            cache_manager=cache_export_manager,
            import_adapter=import_adapter,
            cluster_scale_down_timeout=config.cluster_scale_down_timeout,
            cluster_shutdown_timeout=config.cluster_shutdown_timeout,
        )
        try:
            yield {
                "mcs": mcs,
            }
        finally:
            logger.info("Waiting for metrics calculation service to close")
            await mcs.close()
            if temp_dir:
                logger.info("Removing temp dir")
                shutil.rmtree(temp_dir, ignore_errors=True)

    return initialize_app


def app_factory(lifespan_factory: AppLifespanFactory[AppConfig], config: AppConfig):
    logger.debug(f"loading application with config: {config}")
    app = setup_app(config, lifespan=lifespan_factory(config))
    return app


class ApplicationStateStorage(t.Protocol):
    @property
    def state(self) -> State: ...


def get_mcs(storage: ApplicationStateStorage) -> MetricsCalculationService:
    mcs = storage.state.mcs
    assert mcs is not None
    return t.cast(MetricsCalculationService, mcs)


def setup_app(config: AppConfig, lifespan: t.Callable[[FastAPI], t.Any]):
    # Dependency to get the cluster manager

    app = FastAPI(lifespan=lifespan)

    @app.get("/status")
    async def get_status():
        """Liveness endpoint"""
        return {"status": "Service is running"}

    @app.post("/cluster/start")
    async def start_cluster(
        request: Request,
        start_request: ClusterStartRequest,
    ):
        """Start a Dask cluster in an idempotent way.

        If the cluster is already running, it will not be restarted.
        """
        state = get_mcs(request)
        return await state.start_cluster(start_request)

    @app.post("/cluster/stop")
    async def stop_cluster(request: Request):
        """Stop the Dask cluster"""
        state = get_mcs(request)
        manager = state.cluster_manager
        return await manager.stop_cluster()

    @app.get("/cluster/status")
    async def get_cluster_status(request: Request):
        """Get the current Dask cluster status"""
        state = get_mcs(request)
        manager = state.cluster_manager
        return await manager.get_cluster_status()

    @app.post("/job/submit")
    async def submit_job(
        request: Request,
        input: JobSubmitRequest,
    ):
        """Submits a Dask job for calculation"""
        service = get_mcs(request)
        return await service.submit_job(input)

    @app.get("/job/status/{job_id}")
    async def get_job_status(
        request: Request,
        job_id: str,
    ):
        """Get the status of a job"""
        include_stats = (
            request.query_params.get("include_stats", "false").lower() == "true"
        )
        service = get_mcs(request)
        return await service.get_job_status(job_id, include_stats=include_stats)

    @app.websocket("/job/status/{job_id}/ws")
    async def job_status_ws(
        websocket: WebSocket,
        job_id: str,
    ):
        """Websocket endpoint for job status updates"""
        service = get_mcs(websocket)
        update_queue: asyncio.Queue[JobStatusResponse] = asyncio.Queue()

        await websocket.accept()

        async def listener(job_status_response: JobStatusResponse):
            logger.debug(f"Received job status update: {job_status_response}")
            await update_queue.put(job_status_response)

        stop_listening = await service.listen_for_job_updates(job_id, listener)

        count = 0

        try:
            while True:
                count += 1
                # Send a ping every XX seconds to keep the connection alive
                if count % config.websocket_ping_seconds == 0:
                    logger.debug(f"Websocket state: {websocket.client_state}")
                    await websocket.send_text(PingResponse().model_dump_json())
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    logger.debug("Websocket disconnected while waiting for job updates")
                    break
                try:
                    update = await asyncio.wait_for(update_queue.get(), timeout=1)
                except asyncio.TimeoutError:
                    continue
                await websocket.send_text(update.model_dump_json())
                if update.status in (QueryJobStatus.COMPLETED, QueryJobStatus.FAILED):
                    logger.debug("Job completed, stopping listening")
                    break
        except (WebSocketDisconnect, ClientDisconnected):
            logger.debug("Websocket disconnected")
            stop_listening()
            await websocket.close()
        else:
            stop_listening()
            await websocket.close()

    @app.post("/cache/manual")
    async def add_existing_exported_table_references(
        request: Request, input: ExportedTableLoadRequest
    ):
        """Add a table export to the cache"""
        service = get_mcs(request)
        await service.add_existing_exported_table_references(input.map)
        return EmptyResponse()

    # @app.websocket("/ws")
    # async def websocket_endpoint(websocket: WebSocket):
    #     await websocket.accept()

    #     service = get_mcs(websocket)

    #     response_queue: asyncio.Queue[MCSResponseTypes] = asyncio.Queue()
    #     request_tasks: t.List[asyncio.Task[None]] = []

    #     async def receive_request():
    #         return await websocket.receive_text()

    #     async def receive_response():
    #         return await response_queue.get()

    #     async def send_response(response: MCSResponseTypes):
    #         await websocket.send_text(
    #             ServiceResponse(type=response.type, response=response).model_dump_json()
    #         )

    #     async def request_router(mcs_request_str: str):
    #         try:
    #             mcs_request = ServiceRequest.model_validate_json(mcs_request_str)
    #         except pydantic.ValidationError as e:
    #             await response_queue.put(ErrorResponse(message=str(e)))
    #             return
    #         print(mcs_request)

    #     try:
    #         mcs_request_task = asyncio.create_task(receive_request())
    #         mcs_response_task = asyncio.create_task(receive_response())
    #         pending: t.Set[asyncio.Task[str] | asyncio.Task[MCSResponseTypes]] = {
    #             mcs_request_task,
    #             mcs_response_task,
    #         }
    #         while True:
    #             done, pending = await asyncio.wait(
    #                 pending,
    #                 return_when=asyncio.FIRST_COMPLETED,
    #             )
    #             for task in done:
    #                 if task == mcs_request_task:
    #                     mcs_request_str = t.cast(str, await mcs_request_task)

    #                     request_tasks.append(
    #                         asyncio.create_task(request_router(mcs_request_str))
    #                     )
    #                     mcs_request_task = asyncio.create_task(receive_request())
    #                     pending.add(mcs_request_task)
    #                 else:
    #                     response = t.cast(MCSResponseTypes, await mcs_response_task)
    #                     await send_response(response)

    #                     mcs_response_task = asyncio.create_task(receive_response())
    #     except Exception as e:
    #         await send_response(ErrorResponse(message=str(e)))
    #     finally:
    #         await websocket.close()

    return app
