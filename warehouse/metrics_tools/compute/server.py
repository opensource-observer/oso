import os
import queue
import typing as t
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from email.mime import application

import trino
from dask.distributed import Client, Future, as_completed, get_worker
from dask.distributed import print as dprint
from dask_kubernetes.operator import make_cluster_spec
from fastapi import Depends, FastAPI, Request
from metrics_tools.compute.cache import TrinoCacheExportManager
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.runner import FakeEngineAdapter, MetricsRunner
from pydantic import BaseModel
from sqlmesh.core.dialect import parse_one

from ..utils import env
from .cluster import ClusterManager, make_new_cluster


@dataclass(kw_only=True)
class ApplicationState:
    id: str
    cluster_manager: ClusterManager
    cache_manager: TrinoCacheExportManager
    job_state: t.Dict[str, str]


@asynccontextmanager
async def initialize_app(app: FastAPI):
    cluster_namespace = env.required_str("METRICS_CLUSTER_NAMESPACE")
    cluster_name = env.required_str("METRICS_CLUSTER_NAME")
    threads = env.required_int("METRICS_CLUSTER_WORKER_THREADS", 16)
    image_tag = env.required_str("METRICS_CLUSTER_WORKER_IMAGE_TAG")
    gcs_bucket = env.required_str("METRICS_GCS_BUCKET")
    gcs_key_id = env.required_str("METRICS_GCS_KEY_ID")
    gcs_secret = env.required_str("METRICS_GCS_SECRET")
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
        f"ghcr.io/opensource-observer/dagster-dask:{image_tag}",
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
    yield {
        "app_state": ApplicationState(
            id=str(uuid.uuid4()),
            cluster_manager=cluster_manager,
            job_state={},
            cache_manager=TrinoCacheExportManager(trino_connection, gcs_bucket),
        )
    }
    cluster_manager.close()


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
def get_application_state(request: Request) -> ApplicationState:
    app_state = request.state.app_state
    assert app_state is not None
    return t.cast(ApplicationState, app_state)


app = FastAPI()


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
    request: Request,
    start_request: ClusterStartRequest,
):
    """
    Start a Dask cluster in an idempotent way
    """
    state = get_application_state(request)
    manager = state.cluster_manager
    return manager.start_cluster(start_request.min_size, start_request.max_size)


@app.get("/cluster/status")
async def get_cluster_status(request: Request):
    """
    Get the current Dask cluster status
    """
    state = get_application_state(request)
    manager = state.cluster_manager
    return manager.get_cluster_status()


@app.post("/job/submit")
async def submit_job(
    request: Request,
    input: QueryInput,
):
    """
    Submits a Dask job for calculation
    """
    # Example job submission using query_input
    state = get_application_state(request)
    manager = state.cluster_manager
    client = manager.client

    # future = client.submit(
    #     lambda q: f"Processed query: {q.query_str}", query_input
    # )  # Replace with actual query logic
    # return {"result": future.result()}

    exported_dependent_tables_map: t.Dict[str, str] = {}

    # Parse the query
    for ref_name, actual_name in input.dependent_tables_map.items():
        # Any deps, use trino to export to gcs
        exported_table_name = state.cache_manager.export_table_for_cache(actual_name)
        exported_dependent_tables_map[ref_name] = exported_table_name

    # rewrite the query for the temporary caches made by trino
    # ex = self.table_rewrite(input.query_str, exported_dependent_tables_map)
    # if len(ex) != 1:
    #     raise Exception("unexpected number of expressions")

    rewritten_query = parse_one(input.query_str).sql(dialect="duckdb")
    # columns = input.to_column_names()

    # def gen():
    #     futures: t.List[concurrent.futures.Future[pd.DataFrame]] = []
    #     for rendered_query in runner.render_rolling_queries(input.start, input.end):
    #         future = asyncio.run_coroutine_threadsafe(
    #             async_gen_batch(self.engine, rendered_query, columns),
    #             self.loop_loop,
    #         )
    #         futures.append(future)
    #     for res in concurrent.futures.as_completed(futures):
    #         yield pa.RecordBatch.from_pandas(res.result())

    def gen_with_dask(
        rewritten_query: str,
        input: QueryInput,
        exported_dependent_tables_map: t.Dict[str, str],
        download_queue: queue.Queue[Future],
    ):
        client = state.cluster_manager.client
        futures: t.List[Future] = []
        current_batch: t.List[str] = []
        task_ids: t.List[int] = []

        runner = MetricsRunner.from_engine_adapter(
            FakeEngineAdapter("duckdb"),
            rewritten_query,
            input.ref,
            input.locals,
        )

        task_id = 0
        for rendered_query in runner.render_rolling_queries(input.start, input.end):
            current_batch.append(rendered_query)
            if len(current_batch) >= input.batch_size:
                future = client.submit(
                    execute_duckdb_load,
                    task_id,
                    current_batch[:],
                    exported_dependent_tables_map,
                )
                futures.append(future)
                current_batch = []
                task_ids.append(task_id)
                task_id += 1
        if len(current_batch) > 0:
            future = client.submit(
                execute_duckdb_load,
                task_id,
                current_batch[:],
                exported_dependent_tables_map,
            )
            futures.append(future)
            task_ids.append(task_id)
            task_id += 1

        completed_batches = 0
        total_batches = len(futures)
        for future in as_completed(futures):
            completed_batches += 1
            logger.info(f"progress received [{completed_batches}/{total_batches}]")
            future = t.cast(Future, future)
            if future.cancelled:
                if future.done():
                    logger.info("future actually done???")
                else:
                    logger.error("future cancelled. skipping for now?")
                    print(future)
                    print(future.result() is not None)
                    continue
            download_queue.put(future)
        return task_ids

    def downloader(
        kill_event: threading.Event,
        download_queue: queue.Queue[Future],
        res_queue: queue.Queue[ResultQueueItem],
    ):
        logger.debug("waiting for download")
        while True:
            try:
                future = download_queue.get(timeout=0.1)
                try:
                    item = t.cast(DuckdbLoadedItem, future.result())
                    record_batch = pa.RecordBatch.from_pandas(item.df)
                    res_queue.put(
                        ResultQueueItem(
                            id=item.id,
                            record_batch=record_batch,
                        )
                    )
                    logger.debug("download completed")
                finally:
                    download_queue.task_done()
            except queue.Empty:
                if kill_event.is_set():
                    logger.debug("shutting down downloader")
                    return
            if kill_event.is_set() and not download_queue.empty():
                logger.debug("shutting down downloader prematurely")
                return

    def gen_record_batches(size: int):
        download_queue: queue.Queue[Future] = queue.Queue(maxsize=size)
        res_queue: queue.Queue[ResultQueueItem] = queue.Queue(maxsize=size)
        kill_event = threading.Event()
        result_queue_timeout = 5.0
        max_result_timeout = 300

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.downloader_count + 5
        ) as executor:
            dask_thread = executor.submit(
                gen_with_dask,
                rewritten_query,
                input,
                exported_dependent_tables_map,
                download_queue,
            )
            downloaders = []
            for i in range(self.downloader_count):
                downloaders.append(
                    executor.submit(downloader, kill_event, download_queue, res_queue)
                )

            wait_retries = 0

            completed_task_ids: t.Set[int] = set()
            task_ids: t.Optional[t.Set[int]] = None

            while task_ids != completed_task_ids:
                try:
                    result = res_queue.get(timeout=result_queue_timeout)
                    wait_retries = 0
                    logger.debug("sending batch to client")

                    completed_task_ids.add(result.id)

                    yield result.record_batch
                except queue.Empty:
                    wait_retries += 1
                if task_ids is None:
                    # If the dask thread is done we know if we can check for completion
                    if dask_thread.done():
                        task_ids = set(dask_thread.result())
                else:
                    # If we have waited longer then 15 mins let's stop waiting
                    current_wait_time = wait_retries * result_queue_timeout
                    if current_wait_time > max_result_timeout:
                        logger.debug(
                            "record batches might be completed. with some kind of error"
                        )
                        break
            kill_event.set()
            logger.debug("waiting for the downloaders to shutdown")
            executor.shutdown(cancel_futures=True)

    logger.debug(
        f"Distributing query for {input.start} to {input.end}: {rewritten_query}"
    )
    try:
        return fl.GeneratorStream(
            input.to_arrow_schema(),
            gen_record_batches(size=self.queue_size),
        )
    except Exception as e:
        print("caught error")
        logger.error("Caught error generating stream", exc_info=e)
        raise e
