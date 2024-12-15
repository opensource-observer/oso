"""Main interface for computing metrics"""

import asyncio
import copy
import logging
import os
import typing as t
import uuid
from datetime import datetime

from dask.distributed import CancelledError, Future
from metrics_tools.compute.result import DBImportAdapter
from metrics_tools.compute.worker import execute_duckdb_load
from metrics_tools.runner import FakeEngineAdapter, MetricsRunner

from .cache import CacheExportManager
from .cluster import ClusterManager
from .types import (
    ClusterStartRequest,
    ClusterStatus,
    ColumnsDefinition,
    ExportReference,
    ExportType,
    QueryJobProgress,
    QueryJobState,
    QueryJobStatus,
    QueryJobStatusResponse,
    QueryJobSubmitRequest,
    QueryJobSubmitResponse,
    QueryJobUpdate,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JobFailed(Exception):
    pass


class JobTasksFailed(JobFailed):
    exceptions: t.List[Exception]
    failures: int

    def __init__(self, job_id: str, failures: int, exceptions: t.List[Exception]):
        self.failures = failures
        self.exceptions = exceptions
        super().__init__(
            f"job[{job_id}] failed with {failures} failures and {len(exceptions)} exceptions"
        )


class MetricsCalculationService:
    id: str
    gcs_bucket: str
    cluster_manager: ClusterManager
    cache_manager: CacheExportManager
    job_state: t.Dict[str, QueryJobState]
    job_tasks: t.Dict[str, asyncio.Task]
    job_state_lock: asyncio.Lock
    logger: logging.Logger

    @classmethod
    def setup(
        cls,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: CacheExportManager,
        import_adapter: DBImportAdapter,
        log_override: t.Optional[logging.Logger] = None,
    ):
        service = cls(
            id,
            gcs_bucket,
            result_path_prefix,
            cluster_manager,
            cache_manager,
            import_adapter=import_adapter,
            log_override=log_override,
        )
        return service

    def __init__(
        self,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: CacheExportManager,
        import_adapter: DBImportAdapter,
        log_override: t.Optional[logging.Logger] = None,
    ):
        self.id = id
        self.gcs_bucket = gcs_bucket
        self.result_path_prefix = result_path_prefix
        self.cluster_manager = cluster_manager
        self.cache_manager = cache_manager
        self.import_adapter = import_adapter
        self.job_state = {}
        self.job_tasks = {}
        self.job_state_lock = asyncio.Lock()
        self.logger = log_override or logger

    async def handle_query_job_submit_request(
        self,
        job_id: str,
        result_path_base: str,
        input: QueryJobSubmitRequest,
        export_reference: ExportReference,
    ):
        try:
            await self._handle_query_job_submit_request(
                job_id, result_path_base, input, export_reference
            )
        except Exception as e:
            self.logger.error(f"job[{job_id}] failed with exception: {e}")
            await self._notify_job_failed(job_id, 0, 0)

    async def _handle_query_job_submit_request(
        self,
        job_id: str,
        result_path_base: str,
        input: QueryJobSubmitRequest,
        export_reference: ExportReference,
    ):
        self.logger.debug(f"job[{job_id}] waiting for cluster to be ready")
        await self.cluster_manager.wait_for_ready()
        self.logger.debug(f"job[{job_id}] cluster ready")

        self.logger.debug(f"job[{job_id}] waiting for dependencies to be exported")
        try:
            exported_dependent_tables_map = await self.resolve_dependent_tables(input)
        except Exception as e:
            self.logger.error(f"job[{job_id}] failed to export dependencies: {e}")
            await self._notify_job_failed(job_id, 0, 0)
            return
        self.logger.debug(f"job[{job_id}] dependencies exported")

        tasks = await self._batch_query_to_scheduler(
            job_id, result_path_base, input, exported_dependent_tables_map
        )

        total = len(tasks)
        completed = 0

        # In the future we should replace this with the python 3.13 version of
        # this.
        try:
            await self._monitor_query_task_progress(job_id, tasks)
        except JobTasksFailed as e:
            exceptions = e.exceptions
            self.logger.error(e)
            await self._notify_job_failed(job_id, completed, total)
            if len(exceptions) > 0:
                for e in exceptions:
                    self.logger.error(f"job[{job_id}] exception received: {e}")
            raise e

        # Import the final result into the database
        self.logger.info("job[{job_id}]: importing final result into the database")
        await self.import_adapter.import_reference(export_reference)

        self.logger.debug(f"job[{job_id}]: notifying job completed")
        await self._notify_job_completed(job_id, completed, total)

    async def _batch_query_to_scheduler(
        self,
        job_id: str,
        result_path_base: str,
        input: QueryJobSubmitRequest,
        exported_dependent_tables_map: t.Dict[str, ExportReference],
    ):
        """Given a query job: break down into batches and submit to the scheduler"""
        tasks: t.List[Future] = []

        client = await self.cluster_manager.client
        async for batch_id, batch in self.generate_query_batches(
            input, input.batch_size
        ):
            task_id = f"{job_id}-{batch_id}"
            result_path = os.path.join(result_path_base, job_id, f"{batch_id}.parquet")

            self.logger.debug(f"job[{job_id}]: Submitting task {task_id}")

            # dependencies = {
            #     table: to_jsonable_python(reference)
            #     for table, reference in exported_dependent_tables_map.items()
            # }

            task = client.submit(
                execute_duckdb_load,
                job_id,
                task_id,
                result_path,
                batch,
                exported_dependent_tables_map,
                retries=input.retries,
            )

            self.logger.debug(f"job[{job_id}]: Submitted task {task_id}")
            tasks.append(task)
        return tasks

    async def _monitor_query_task_progress(self, job_id: str, tasks: t.List[Future]):
        total = len(tasks)
        completed = 0
        failures = 0
        exceptions = []

        # In the future we should replace this with the python 3.13 version of
        # this.
        for finished in asyncio.as_completed(tasks):
            try:
                task_id = await finished
                completed += 1
                self.logger.info(f"job[{job_id}] progress: {completed}/{total}")
                await self._notify_job_updated(job_id, completed, total)
                self.logger.debug(
                    f"job[{job_id}] finished notifying update: {completed}/{total}"
                )
            except CancelledError as e:
                failures += 1
                self.logger.error(f"job[{job_id}] task cancelled {e.args}")
                continue
            except Exception as e:
                failures += 1
                exceptions.append(e)
                self.logger.error(f"job[{job_id}] task failed with exception: {e}")
                continue
            self.logger.debug(f"job[{job_id}] awaiting finished")

            await self._notify_job_updated(job_id, completed, total)
            self.logger.info(f"job[{job_id}] task_id={task_id} finished")
        if failures > 0:
            raise JobTasksFailed(job_id, failures, exceptions)

    async def close(self):
        await self.cluster_manager.close()
        await self.cache_manager.stop()

    async def start_cluster(self, start_request: ClusterStartRequest) -> ClusterStatus:
        self.logger.debug("starting cluster")
        return await self.cluster_manager.start_cluster(
            start_request.min_size, start_request.max_size
        )

    async def get_cluster_status(self):
        return self.cluster_manager.get_cluster_status()

    async def submit_job(self, input: QueryJobSubmitRequest):
        """Submit a job to the cluster to compute the metrics"""
        self.logger.debug("submitting job")
        job_id = str(uuid.uuid4())

        self.logger.debug(
            f"job[{job_id}] logging request: {input.model_dump_json(indent=2)}"
        )

        # Files are organized in a way that can be searched by date such that we
        # can easily clean old files
        result_path_base = os.path.join(
            self.result_path_prefix,
            input.execution_time.strftime("%Y/%m/%d/%H"),
            job_id,
        )
        result_path = os.path.join(
            f"gs://{self.gcs_bucket}",
            result_path_base,
            "*.parquet",
        )

        final_expected_reference = await self.import_adapter.translate_reference(
            ExportReference(
                table_name=job_id,
                type=ExportType.GCS,
                columns=ColumnsDefinition(columns=input.columns, dialect=input.dialect),
                payload={"gcs_path": result_path},
            )
        )

        await self._notify_job_pending(job_id, 1)
        task = asyncio.create_task(
            self.handle_query_job_submit_request(
                job_id,
                result_path_base,
                input,
                final_expected_reference,
            )
        )
        async with self.job_state_lock:
            self.job_tasks[job_id] = task

        return QueryJobSubmitResponse(
            job_id=job_id,
            export_reference=final_expected_reference,
        )

    async def _notify_job_pending(self, job_id: str, total: int):
        await self._set_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.PENDING,
                progress=QueryJobProgress(completed=0, total=total),
            ),
        )

    async def _notify_job_updated(self, job_id: str, completed: int, total: int):
        await self._set_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.RUNNING,
                progress=QueryJobProgress(completed=completed, total=total),
            ),
        )

    async def _notify_job_completed(self, job_id: str, completed: int, total: int):
        await self._set_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.COMPLETED,
                progress=QueryJobProgress(completed=completed, total=total),
            ),
        )

    async def _notify_job_failed(self, job_id: str, completed: int, total: int):
        await self._set_job_state(
            job_id,
            QueryJobUpdate(
                updated_at=datetime.now(),
                status=QueryJobStatus.FAILED,
                progress=QueryJobProgress(completed=completed, total=total),
            ),
        )

    async def _set_job_state(
        self,
        job_id: str,
        update: QueryJobUpdate,
    ):
        self.logger.debug(f"job[{job_id}] status={update.status}")
        async with self.job_state_lock:
            if update.status == QueryJobStatus.PENDING:
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
                    del self.job_tasks[job_id]

    async def _get_job_state(self, job_id: str):
        """Get the current state of a job as a deep copy (to prevent
        mutation)"""
        async with self.job_state_lock:
            state = copy.deepcopy(self.job_state.get(job_id))
        return state

    async def generate_query_batches(
        self, input: QueryJobSubmitRequest, batch_size: int
    ):
        runner = MetricsRunner.from_engine_adapter(
            FakeEngineAdapter("duckdb"),
            input.query_as("duckdb"),
            input.ref,
            input.locals,
        )

        batch: t.List[str] = []
        batch_num = 0

        async for rendered_query in runner.render_rolling_queries_async(
            input.start, input.end
        ):
            batch.append(rendered_query)
            if len(batch) >= batch_size:
                yield (batch_num, batch)
                batch = []
                batch_num += 1
        if len(batch) > 0:
            yield (batch_num, batch)

    async def resolve_dependent_tables(self, input: QueryJobSubmitRequest):
        """Resolve the dependent tables for the given input and returns the
        associate export references"""

        # Dependent tables come in the form:
        # { reference_table_name: actual_table_table }

        # The reference_table_name is something like
        # "metrics.events_daily_to_artifact". The actual_table_name is something
        # like
        # "sqlmesh__metrics.events_daily_to_artifact__some_system_generated_id"
        dependent_tables_map = input.dependent_tables_map
        tables_to_export = list(dependent_tables_map.values())

        # The cache manager will generate random export references for each
        # table you ask to cache for use in metrics calculations. However it is
        # not aware of the `reference_table_name` that the user provides. We
        # need to resolve the actual table names to the export references
        reverse_dependent_tables_map = {v: k for k, v in dependent_tables_map.items()}

        # First use the cache manager to resolve the export references
        references = await self.cache_manager.resolve_export_references(
            tables_to_export, input.execution_time
        )
        self.logger.debug(f"resolved references: {references}")

        # Now map the reference_table_names to the export references
        exported_dependent_tables_map = {
            reverse_dependent_tables_map[actual_name]: reference
            for actual_name, reference in references.items()
        }

        return exported_dependent_tables_map

    async def get_job_status(
        self, job_id: str, include_stats: bool = False
    ) -> QueryJobStatusResponse:
        state = await self._get_job_state(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")
        return state.as_response(include_stats=include_stats)

    async def add_existing_exported_table_references(
        self, update: t.Dict[str, ExportReference]
    ):
        """This is mostly used for testing purposes, but allows us to load a
        previously cached table's reference into the cache manager"""
        await self.cache_manager.add_export_table_references(update)

    async def inspect_exported_table_references(self):
        return await self.cache_manager.inspect_export_table_references()
