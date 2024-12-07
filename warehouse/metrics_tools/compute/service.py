"""Main interface for computing metrics"""

from datetime import datetime
import os
import queue
import copy
import typing as t
import uuid
import logging
import threading

from metrics_tools.compute.worker import execute_duckdb_load
from metrics_tools.runner import FakeEngineAdapter, MetricsRunner
from dask.distributed import Future, as_completed

from .cache import TrinoCacheExportManager
from .cluster import ClusterManager
from .types import (
    ClusterStartRequest,
    QueryJobUpdate,
    QueryJobSubmitRequest,
    ClusterStatus,
    QueryJobSubmitResponse,
    QueryJobStatusResponse,
    QueryJobState,
    QueryJobStatus,
    QueryJobProgress,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MetricsCalculationService:
    id: str
    gcs_bucket: str
    cluster_manager: ClusterManager
    cache_manager: TrinoCacheExportManager
    job_state: t.Dict[str, QueryJobState]
    job_threads: t.Dict[str, threading.Thread]
    job_state_lock: threading.Lock
    logger: logging.Logger
    job_update_queue: queue.Queue[
        t.Tuple[str, QueryJobUpdate, t.Optional[threading.Thread]]
    ]
    stop_event: threading.Event

    @classmethod
    def setup(
        cls,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: TrinoCacheExportManager,
        log_override: t.Optional[logging.Logger] = None,
    ):
        service = cls(
            id,
            gcs_bucket,
            result_path_prefix,
            cluster_manager,
            cache_manager,
            log_override=log_override,
        )
        service.start_job_state_listener()
        return service

    def __init__(
        self,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: TrinoCacheExportManager,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.id = id
        self.gcs_bucket = gcs_bucket
        self.result_path_prefix = result_path_prefix
        self.cluster_manager = cluster_manager
        self.cache_manager = cache_manager
        self.job_state = {}
        self.job_threads = {}
        self.job_state_lock = threading.Lock()
        self.logger = log_override or logger
        self.job_update_queue = queue.Queue(maxsize=1000)
        self.stop_event = threading.Event()

    def wait_for_job_state(self):
        """Wait for job state updates indefinitely"""
        while True:
            try:
                job_id, job_state, thread = self.job_update_queue.get(timeout=2)
            except queue.Empty:
                if self.stop_event.is_set():
                    self.logger.info("Stopping job state listener")
                    break
                continue
            self.logger.info(f"Received job state update: {job_state}")
            self._set_job_state(job_id, job_state, thread=thread)

    def start_job_state_listener(self):
        thread = threading.Thread(target=self.wait_for_job_state)
        thread.start()

    def close(self):
        self.cluster_manager.close()
        self.stop_event.set()

    def start_cluster(self, start_request: ClusterStartRequest) -> ClusterStatus:
        self.logger.debug("starting cluster")
        return self.cluster_manager.start_cluster(
            start_request.min_size, start_request.max_size
        )

    def get_cluster_status(self):
        return self.cluster_manager.get_cluster_status()

    def submit_job(self, input: QueryJobSubmitRequest):
        """Submit a job to the cluster to compute the metrics"""
        self.logger.debug("submitting job")
        job_id = str(uuid.uuid4())
        client = self.cluster_manager.client

        # Load any dependent tables into an easily accessible area on gcs
        exported_dependent_tables_map = self.load_dependent_tables(input)

        futures: t.List[Future] = []

        result_path_base = os.path.join(self.result_path_prefix, job_id)

        for batch_id, batch in self.generate_query_batches(input, input.batch_size):
            task_id = f"{job_id}-{batch_id}"
            result_path = os.path.join(result_path_base, job_id, f"{batch_id}.parquet")

            self.logger.info(f"job[{job_id}]: Submitting task {task_id}")
            future = client.submit(
                execute_duckdb_load,
                job_id,
                task_id,
                result_path,
                batch,
                dependencies=exported_dependent_tables_map,
            )
            futures.append(future)

        thread = threading.Thread(
            target=self._wait_for_job_futures, args=(job_id, futures)
        )
        self._notify_job_pending(job_id, len(futures), thread)
        thread.start()
        result_path = os.path.join(
            f"gs://{self.gcs_bucket}", result_path_base, "*.parquet"
        )

        return QueryJobSubmitResponse(job_id=job_id, result_path=result_path)

    def _wait_for_job_futures(self, job_id: str, futures: t.List[Future]):
        completed_batches = 0
        total_batches = len(futures)
        exceptions = []
        failed = False
        try:
            for future in as_completed(futures):
                completed_batches += 1
                self._notify_job_updated(job_id, completed_batches, total_batches)
                self.logger.info(
                    f"job[{job_id}]: Progress {completed_batches}/{total_batches}"
                )
                future = t.cast(Future, future)
                if future.status == "finished":
                    task_id = future.result()
                    self.logger.info(f"job[{job_id}] task_id={task_id} finished")
                elif future.status == "error":
                    self.logger.error(
                        f"job[{job_id}] Future error: {future.exception()}"
                    )
                    exceptions.append(future.exception())
                    failed = True
                    continue
                else:
                    self.logger.error(
                        f'job[{job_id}] Unsuccessful future state "{future.status}" received'
                    )
                    failed = True
                    continue
            self.logger.info(f"job[{job_id}]: done")
        except Exception as e:
            self.logger.error(f"job[{job_id}]: Failed with error: {e}")
            self._notify_job_failed(job_id, completed_batches, total_batches)

        if len(exceptions) > 0 or failed:
            self.logger.error(f"job[{job_id}]: received {len(exceptions)} exceptions")
            self._notify_job_failed(job_id, completed_batches, total_batches)

        self.logger.info(f"job[{job_id}]: completed")
        self._notify_job_completed(job_id, completed_batches, total_batches)

    def _notify_job_pending(self, job_id: str, total: int, thread: threading.Thread):
        self._queue_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.PENDING,
                progress=QueryJobProgress(completed=0, total=total),
            ),
            thread=thread,
        )

    def _notify_job_updated(self, job_id: str, completed: int, total: int):
        self._queue_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.RUNNING,
                progress=QueryJobProgress(completed=completed, total=total),
            ),
        )

    def _notify_job_completed(self, job_id: str, completed: int, total: int):
        self._queue_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.COMPLETED,
                progress=QueryJobProgress(completed=completed, total=total),
            ),
        )

    def _notify_job_failed(self, job_id: str, completed: int, total: int):
        self._queue_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.FAILED,
                progress=QueryJobProgress(completed=completed, total=total),
            ),
        )

    def _queue_job_state(
        self,
        job_id: str,
        state: QueryJobUpdate,
        thread: t.Optional[threading.Thread] = None,
    ):
        self.job_update_queue.put((job_id, state, thread))

    def _set_job_state(
        self,
        job_id: str,
        update: QueryJobUpdate,
        thread: t.Optional[threading.Thread] = None,
    ):
        with self.job_state_lock:
            if update.status == QueryJobStatus.PENDING:
                assert thread is not None
                self.job_threads[job_id] = thread
                self.job_state[job_id] = QueryJobState(
                    job_id=job_id,
                    created_at=update.updated_at,
                    updates=[update],
                )
            else:
                state = self.job_state.get(job_id)
                if not state:
                    raise ValueError(f"Job {job_id} not found")

                state.updates.append(update)
                self.job_state[job_id] = state

                if (
                    update.status == QueryJobStatus.COMPLETED
                    or update.status == QueryJobStatus.FAILED
                ):
                    del self.job_threads[job_id]

    def _get_job_state(self, job_id: str):
        """Get the current state of a job as a deep copy (to prevent
        mutation)"""
        with self.job_state_lock:
            state = copy.deepcopy(self.job_state.get(job_id))
        return state

    def generate_query_batches(self, input: QueryJobSubmitRequest, batch_size: int):
        runner = MetricsRunner.from_engine_adapter(
            FakeEngineAdapter("duckdb"),
            input.query_as("duckdb"),
            input.ref,
            input.locals,
        )

        batch: t.List[str] = []
        batch_num = 0
        for rendered_query in runner.render_rolling_queries(input.start, input.end):
            batch.append(rendered_query)
            if len(batch) >= batch_size:
                yield (batch_num, batch)
                batch = []
                batch_num += 1
        if len(batch) > 0:
            yield (batch_num, batch)

    def load_dependent_tables(self, input: QueryJobSubmitRequest):
        exported_dependent_tables_map: t.Dict[str, str] = {}
        for ref_name, actual_name in input.dependent_tables_map.items():
            # Any deps, use trino to export to gcs
            exported_table_name = self.cache_manager.export_table_for_cache(actual_name)
            exported_dependent_tables_map[ref_name] = exported_table_name
        return exported_dependent_tables_map

    def get_job_status(
        self, job_id: str, include_stats: bool = False
    ) -> QueryJobStatusResponse:
        state = self._get_job_state(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")
        return state.as_response(include_stats=include_stats)

    def add_existing_exported_table_references(self, update: t.Dict[str, str]):
        """This is mostly used for testing purposes, but allows us to load a
        previously cached table's reference into the cache manager"""
        self.cache_manager.add_export_table_references(update)
