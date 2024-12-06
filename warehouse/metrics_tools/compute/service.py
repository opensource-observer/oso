"""Main interface for computing metrics"""

import os
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
    QueryJobSubmitInput,
    ClusterStatus,
    QueryJobSubmitResponse,
    QueryJobStatusResponse,
)

logger = logging.getLogger(__name__)


class MetricsCalculationService:
    id: str
    gcs_bucket: str
    cluster_manager: ClusterManager
    cache_manager: TrinoCacheExportManager
    job_state: t.Dict[str, str]
    job_threads: t.Dict[str, threading.Thread]
    job_state_lock: threading.Lock

    @classmethod
    def setup(
        cls,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: TrinoCacheExportManager,
    ):
        return cls(id, gcs_bucket, result_path_prefix, cluster_manager, cache_manager)

    def __init__(
        self,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: TrinoCacheExportManager,
    ):
        self.id = id
        self.gcs_bucket = gcs_bucket
        self.result_path_prefix = result_path_prefix
        self.cluster_manager = cluster_manager
        self.cache_manager = cache_manager
        self.job_state = {}
        self.job_threads = {}
        self.job_state_lock = threading.Lock()

    def start_cluster(self, start_request: ClusterStartRequest) -> ClusterStatus:
        return self.cluster_manager.start_cluster(
            start_request.min_size, start_request.max_size
        )

    def get_cluster_status(self):
        return self.cluster_manager.get_cluster_status()

    def submit_job(self, input: QueryJobSubmitInput):
        """Submit a job to the cluster to compute the metrics"""
        job_id = str(uuid.uuid4())
        client = self.cluster_manager.client

        # Load any dependent tables into an easily accessible area on gcs
        exported_dependent_tables_map = self.load_dependent_tables(input)

        futures: t.List[Future] = []

        result_path_base = os.path.join(self.result_path_prefix, job_id)

        for batch_id, batch in self.generate_query_batches(input, input.batch_size):
            task_id = f"{job_id}-{batch_id}"
            result_path = os.path.join(result_path_base, job_id, f"{batch_id}.parquet")
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
        self._set_job_started(job_id, thread)
        thread.start()
        result_path = os.path.join(
            f"gs://{self.gcs_bucket}", result_path_base, "*.parquet"
        )

        return QueryJobSubmitResponse(job_id=job_id, result_path=result_path)

    def _wait_for_job_futures(self, job_id: str, futures: t.List[Future]):
        completed_batches = 0
        total_batches = len(futures)
        try:
            for future in as_completed(futures):
                completed_batches += 1
                logger.info(
                    f"job[{job_id}]: Progress {completed_batches}/{total_batches}"
                )
                future = t.cast(Future, future)
                if future.cancelled:
                    if future.done():
                        logger.info("future actually done???")
                    else:
                        logger.error("future cancelled. skipping for now?")
                        continue
            logger.info(f"job[{job_id}]: Completed")
            self._set_job_completed(job_id)
        except Exception as e:
            logger.error(f"job[{job_id}]: Failed with error: {e}")
            self._set_job_failed(job_id)

    def _set_job_started(self, job_id: str, thread: threading.Thread):
        self._set_job_state(job_id, "started", thread=thread)

    def _set_job_completed(self, job_id: str):
        self._set_job_state(job_id, "completed", delete_thread=True)

    def _set_job_failed(self, job_id: str):
        self._set_job_state(job_id, "failed", delete_thread=True)

    def _set_job_state(
        self,
        job_id: str,
        state: str,
        thread: t.Optional[threading.Thread] = None,
        delete_thread: bool = False,
    ):
        with self.job_state_lock:
            self.job_state[job_id] = state
            if thread:
                self.job_threads[job_id] = thread
            if delete_thread and job_id in self.job_threads:
                del self.job_threads[job_id]

    def _get_job_state(self, job_id: str):
        with self.job_state_lock:
            state = self.job_state.get(job_id)
        return state

    def generate_query_batches(self, input: QueryJobSubmitInput, batch_size: int):
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

    def load_dependent_tables(self, input: QueryJobSubmitInput):
        exported_dependent_tables_map: t.Dict[str, str] = {}
        for ref_name, actual_name in input.dependent_tables_map.items():
            # Any deps, use trino to export to gcs
            exported_table_name = self.cache_manager.export_table_for_cache(actual_name)
            exported_dependent_tables_map[ref_name] = exported_table_name
        return exported_dependent_tables_map

    def get_job_status(self, job_id: str):
        status = self._get_job_state(job_id)
        if not status:
            raise ValueError(f"Job {job_id} not found")
        return QueryJobStatusResponse(job_id=job_id, status=status)

    def add_manual_exported_table_reference(self, ref_name: str, actual_name: str):
        """This is mostly used for testing purposes, but allows us to load a
        previously cached table's reference into the cache manager"""
        self.cache_manager.add_export_table_reference(ref_name, actual_name)
