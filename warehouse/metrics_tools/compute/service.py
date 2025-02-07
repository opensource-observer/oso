"""Main interface for computing metrics"""

import asyncio
import copy
import logging
import os
import typing as t
import uuid
from datetime import datetime

from dask.distributed import CancelledError
from metrics_tools.compute.result import DBImportAdapter
from metrics_tools.compute.worker import execute_duckdb_load
from metrics_tools.runner import FakeEngineAdapter, MetricsRunner
from pyee.asyncio import AsyncIOEventEmitter

from .cache import CacheExportManager
from .cluster import ClusterManager
from .types import (
    ClusterStartRequest,
    ClusterStatus,
    ColumnsDefinition,
    ExportReference,
    ExportType,
    JobStatusResponse,
    JobSubmitRequest,
    JobSubmitResponse,
    QueryJobState,
    QueryJobStateUpdate,
    QueryJobStatus,
    QueryJobTaskStatus,
    QueryJobTaskUpdate,
    QueryJobUpdate,
    QueryJobUpdateScope,
    TableReference,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class JobError(Exception):
    pass


class JobFailed(JobError):
    exceptions: t.List[Exception]
    cancellations: t.List[str]
    failures: int

    def __init__(
        self,
        job_id: str,
        failures: int,
        exceptions: t.List[Exception],
        cancellations: t.List[str],
    ):
        self.failures = failures
        self.exceptions = exceptions
        self.cancellations = cancellations
        super().__init__(
            f"job[{job_id}] failed with {failures} failures and {len(exceptions)} exceptions and {len(cancellations)} cancellations"
        )


class JobTaskCancelled(JobError):
    task_id: str

    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"task {task_id} was cancelled")


class JobTaskFailed(JobError):
    exception: Exception

    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__(f"task failed with exception: {exception}")


class MetricsCalculationService:
    id: str
    gcs_bucket: str
    cluster_manager: ClusterManager
    cache_manager: CacheExportManager
    last_listener_added_datetime: datetime
    last_listener_removed_datetime: datetime
    listener_count: int
    job_state: t.Dict[str, QueryJobState]
    job_tasks: t.Dict[str, asyncio.Task]
    job_state_lock: asyncio.Lock
    logger: logging.Logger
    daemon: asyncio.Task
    requested_cluster_min_size: int
    requested_cluster_max_size: int

    @classmethod
    def setup(
        cls,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: CacheExportManager,
        import_adapter: DBImportAdapter,
        cluster_scale_down_timeout: int = 300,
        cluster_shutdown_timeout: int = 3600,
        log_override: t.Optional[logging.Logger] = None,
    ):
        service = cls(
            id,
            gcs_bucket,
            result_path_prefix,
            cluster_manager,
            cache_manager,
            cluster_scale_down_timeout=cluster_scale_down_timeout,
            cluster_shutdown_timeout=cluster_shutdown_timeout,
            import_adapter=import_adapter,
            log_override=log_override,
        )
        service.start_daemon()
        return service

    def __init__(
        self,
        id: str,
        gcs_bucket: str,
        result_path_prefix: str,
        cluster_manager: ClusterManager,
        cache_manager: CacheExportManager,
        import_adapter: DBImportAdapter,
        cluster_scale_down_timeout: int = 300,
        cluster_shutdown_timeout: int = 3600,
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
        self.emitter = AsyncIOEventEmitter()
        self.listener_count = 0
        self.requested_cluster_min_size = 0
        self.requested_cluster_max_size = 0
        self.cluster_shutdown_timeout = cluster_shutdown_timeout
        self.cluster_scale_down_timeout = cluster_scale_down_timeout

    async def handle_query_job_submit_request(
        self,
        job_id: str,
        result_path_base: str,
        input: JobSubmitRequest,
        calculation_export: ExportReference,
        final_export: ExportReference,
    ):
        try:
            await self._handle_query_job_submit_request(
                job_id, result_path_base, input, calculation_export, final_export
            )
        except Exception as e:
            self.logger.error(f"job[{job_id}] failed with exception: {e}")
            await self._notify_job_failed(job_id, False, e)

    def start_daemon(self):
        """Starts a daemon coroutine that will run until the service is closed"""
        self.daemon = asyncio.create_task(self._daemon())

    async def _daemon(self):
        scaled_down = False
        shutdown = False
        while True:
            await asyncio.sleep(60)

            # Checks if there are listeners. If 0 and nothing has been added
            # in the last X seconds (cluster_scale_down_timeout) we can scale down the
            # cluster to 0. If nothing has been added in the last Y seconds
            # (cluster_shutdown_timeout) time we can shutdown the entire
            # dask cluster.
            now = datetime.now()
            if self.listener_count == 0:
                last_listener_removed_delta = now - self.last_listener_removed_datetime
                if (
                    last_listener_removed_delta.total_seconds()
                    > self.cluster_scale_down_timeout
                ) and not scaled_down:
                    # If the cluster is already at 0 we don't need to do
                    # anything just make sure everything is stopped
                    scaled_down = True
                    if self.requested_cluster_max_size == 0:
                        await self.cluster_manager.stop_cluster()

                    await self.cluster_manager.start_cluster(
                        0, self.requested_cluster_max_size
                    )

                elif (
                    last_listener_removed_delta.total_seconds()
                    > self.cluster_shutdown_timeout
                ) and not shutdown:
                    await self.cluster_manager.stop_cluster()
                    shutdown = True
                else:
                    # If we are not scaling down or shutting down then we reset these states
                    scaled_down = False
                    shutdown = False

    async def _handle_query_job_submit_request(
        self,
        job_id: str,
        result_path_base: str,
        input: JobSubmitRequest,
        calculation_export: ExportReference,
        final_export: ExportReference,
    ):
        self.logger.debug(f"job[{job_id}] waiting for cluster to be ready")
        await self.cluster_manager.wait_for_ready()
        self.logger.debug(f"job[{job_id}] cluster ready")

        self.logger.debug(f"job[{job_id}] waiting for dependencies to be exported")
        try:
            exported_dependent_tables_map = await self.resolve_dependent_tables(input)
        except Exception as e:
            self.logger.error(f"job[{job_id}] failed to export dependencies: {e}")
            raise e
        self.logger.debug(f"job[{job_id}] dependencies exported")

        tasks = await self._batch_query_to_scheduler(
            job_id, result_path_base, input, exported_dependent_tables_map
        )

        total = len(tasks)
        if total != input.batch_count():
            self.logger.warning(f"job[{job_id}] batch count mismatch")

        exceptions = []
        cancellations = []

        for next_task in asyncio.as_completed(tasks):
            try:
                await next_task
            except JobTaskCancelled as e:
                cancellations.append(e.task_id)
            except JobTaskFailed as e:
                exceptions.append(e.exception)
            except Exception as e:
                self.logger.error(
                    f"job[{job_id}] task failed with uncaught exception: {e}"
                )
                exceptions.append(e)
                # Report failure early for any listening clients. The server
                # will collect all errors for any internal reporting needed
                await self._notify_job_failed(job_id, True, e)

        # If there are any exceptions then we report those as failed and short
        # circuit this method
        if len(exceptions) > 0 or len(cancellations) > 0:
            raise JobFailed(job_id, len(exceptions), exceptions, cancellations)

        # Import the final result into the database
        self.logger.info(f"job[{job_id}]: importing final result into the database")
        await self.import_adapter.import_reference(calculation_export, final_export)

        self.logger.debug(f"job[{job_id}]: notifying job completed")
        await self._notify_job_completed(job_id)

    async def _batch_query_to_scheduler(
        self,
        job_id: str,
        result_path_base: str,
        input: JobSubmitRequest,
        exported_dependent_tables_map: t.Dict[str, ExportReference],
    ):
        """Given a query job: break down into batches and submit to the scheduler"""

        tasks: t.List[asyncio.Task] = []
        count = 0
        async for batch_id, batch in self.generate_query_batches(
            input, input.batch_size
        ):
            if count == 0:
                await self._notify_job_running(job_id)

            task_id = f"{job_id}-{batch_id}"
            result_path = os.path.join(result_path_base, f"{batch_id}.parquet")

            self.logger.debug(f"job[{job_id}]: Submitting task {task_id}")

            task = asyncio.create_task(
                self._submit_query_task_to_scheduler(
                    job_id,
                    task_id,
                    result_path,
                    batch,
                    input.slots,
                    exported_dependent_tables_map,
                    retries=3,
                )
            )
            tasks.append(task)

            self.logger.debug(f"job[{job_id}]: Submitted task {task_id}")
            count += 1
        return tasks

    async def _submit_query_task_to_scheduler(
        self,
        job_id: str,
        task_id: str,
        result_path: str,
        batch: t.List[str],
        slots: int,
        exported_dependent_tables_map: t.Dict[str, ExportReference],
        retries: int,
    ):
        """Submit a single query task to the scheduler"""
        client = await self.cluster_manager.client

        task_future = client.submit(
            execute_duckdb_load,
            job_id,
            task_id,
            result_path,
            batch,
            exported_dependent_tables_map,
            retries=retries,
            key=task_id,
            resources={"slots": slots},
        )

        try:
            await task_future
            self.logger.info(f"job[{job_id}] task_id={task_id} completed")
            await self._notify_job_task_completed(job_id, task_id)
        except CancelledError as e:
            self.logger.error(f"job[{job_id}] task cancelled {e.args}")
            await self._notify_job_task_cancelled(job_id, task_id)
            raise JobTaskCancelled(task_id)
        except Exception as e:
            self.logger.error(f"job[{job_id}] task failed with exception: {e}")
            await self._notify_job_task_failed(job_id, task_id, e)
            raise JobTaskFailed(e)
        return task_id

    async def close(self):
        await self.cluster_manager.close()
        await self.cache_manager.stop()

        self.daemon.cancel()
        try:
            await self.daemon
        except asyncio.CancelledError:
            pass

    async def start_cluster(self, start_request: ClusterStartRequest) -> ClusterStatus:
        self.logger.debug("starting cluster")

        self.requested_cluster_max_size = start_request.max_size
        self.requested_cluster_min_size = start_request.min_size

        return await self.cluster_manager.start_cluster(
            start_request.min_size, start_request.max_size
        )

    async def get_cluster_status(self):
        return self.cluster_manager.get_cluster_status()

    async def submit_job(self, input: JobSubmitRequest):
        """Submit a job to the cluster to compute the metrics"""
        self.logger.debug("submitting job")
        job_id = f"export_{str(uuid.uuid4().hex)}"

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

        # This is the export that the workers should write to
        calculation_export = ExportReference(
            table=TableReference(table_name=job_id),
            type=ExportType.GCS,
            columns=ColumnsDefinition(columns=input.columns, dialect=input.dialect),
            payload={"gcs_path": result_path},
        )

        final_expected_reference = await self.import_adapter.translate_reference(
            calculation_export
        )

        await self._notify_job_pending(job_id, input)
        task = asyncio.create_task(
            self.handle_query_job_submit_request(
                job_id,
                result_path_base,
                input,
                calculation_export,
                final_expected_reference,
            )
        )
        async with self.job_state_lock:
            self.job_tasks[job_id] = task

        return JobSubmitResponse(
            job_id=job_id,
            export_reference=final_expected_reference,
        )

    async def _notify_job_pending(self, job_id: str, input: JobSubmitRequest):
        await self._create_job_state(
            job_id,
            input,
        )

    async def _notify_job_running(self, job_id: str):
        await self._update_job_state(
            job_id,
            QueryJobUpdate.create_job_update(
                payload=QueryJobStateUpdate(
                    status=QueryJobStatus.RUNNING,
                    has_remaining_tasks=True,
                ),
            ),
        )

    async def _notify_job_task_completed(self, job_id: str, task_id: str):
        await self._update_job_state(
            job_id,
            QueryJobUpdate.create_task_update(
                payload=QueryJobTaskUpdate(
                    task_id=task_id,
                    status=QueryJobTaskStatus.SUCCEEDED,
                ),
            ),
        )

    async def _notify_job_task_failed(
        self, job_id: str, task_id: str, exception: Exception
    ):
        await self._update_job_state(
            job_id,
            QueryJobUpdate.create_task_update(
                payload=QueryJobTaskUpdate(
                    task_id=task_id,
                    status=QueryJobTaskStatus.FAILED,
                    exception=str(exception),
                ),
            ),
        )

    async def _notify_job_task_cancelled(self, job_id: str, task_id: str):
        await self._update_job_state(
            job_id,
            QueryJobUpdate.create_task_update(
                payload=QueryJobTaskUpdate(
                    task_id=task_id,
                    status=QueryJobTaskStatus.CANCELLED,
                ),
            ),
        )

    async def _notify_job_completed(self, job_id: str):
        await self._update_job_state(
            job_id,
            QueryJobUpdate.create_job_update(
                payload=QueryJobStateUpdate(
                    status=QueryJobStatus.COMPLETED,
                    has_remaining_tasks=False,
                ),
            ),
        )

    async def _notify_job_failed(
        self,
        job_id: str,
        has_remaining_tasks: bool,
        exception: t.Optional[Exception] = None,
    ):
        await self._update_job_state(
            job_id,
            QueryJobUpdate.create_job_update(
                payload=QueryJobStateUpdate(
                    status=QueryJobStatus.FAILED,
                    has_remaining_tasks=has_remaining_tasks,
                    exception=str(exception) if exception else None,
                ),
            ),
        )

    async def _create_job_state(self, job_id: str, input: JobSubmitRequest):
        async with self.job_state_lock:
            now = datetime.now()
            self.job_state[job_id] = QueryJobState(
                job_id=job_id,
                created_at=now,
                tasks_count=input.batch_count(),
                updates=[
                    QueryJobUpdate(
                        time=now,
                        scope=QueryJobUpdateScope.JOB,
                        payload=QueryJobStateUpdate(
                            status=QueryJobStatus.PENDING,
                            has_remaining_tasks=True,
                        ),
                    )
                ],
            )

            state = self.job_state[job_id]
            self.emit_job_state(job_id, state)

    async def _update_job_state(
        self,
        job_id: str,
        update: QueryJobUpdate,
    ):
        self.logger.debug(f"job[{job_id}] status={update.payload.status}")
        async with self.job_state_lock:
            state = self.job_state.get(job_id)
            assert state is not None, f"job[{job_id}] not found"
            state.update(update)
            self.job_state[job_id] = state
            self.emit_job_state(job_id, state)

    def emit_job_state(self, job_id: str, state: QueryJobState):
        copied_state = copy.deepcopy(state)
        self.logger.info("emitting job update events")
        self.emitter.emit("job_update", job_id, copied_state)
        self.emitter.emit(f"job_update:{job_id}", copied_state)

    async def _get_job_state(self, job_id: str):
        """Get the current state of a job as a deep copy (to prevent
        mutation)"""
        async with self.job_state_lock:
            state = copy.deepcopy(self.job_state.get(job_id))
        return state

    async def generate_query_batches(self, input: JobSubmitRequest, batch_size: int):
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

    async def resolve_dependent_tables(self, input: JobSubmitRequest):
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
    ) -> JobStatusResponse:
        state = await self._get_job_state(job_id)
        if not state:
            raise ValueError(f"Job {job_id} not found")
        return state.as_response(include_stats=include_stats)

    def listen_for_job_updates(
        self, job_id: str, handler: t.Callable[[JobStatusResponse], t.Awaitable[None]]
    ):
        self.last_listener_added_datetime = datetime.now()
        self.listener_count += 1
        self.logger.info(
            f"Adding listener for job[{job_id}]. Total listeners: {self.listener_count}"
        )

        async def convert_to_response(state: QueryJobState):
            self.logger.debug("converting to response")
            return await handler(state.as_response())

        handle = self.emitter.add_listener(f"job_update:{job_id}", convert_to_response)

        def remove_listener():
            self.emitter.remove_listener(f"job_update:{job_id}", handle)
            self.last_listener_removed_datetime = datetime.now()
            self.listener_count -= 1
            self.logger.info(
                f"Removed listener for job[{job_id}]. Total listeners: {self.listener_count}"
            )
            return

        return remove_listener

    async def add_existing_exported_table_references(
        self, update: t.Dict[str, ExportReference]
    ):
        """This is mostly used for testing purposes, but allows us to load a
        previously cached table's reference into the cache manager"""
        await self.cache_manager.add_export_table_references(update)

    async def inspect_exported_table_references(self):
        return await self.cache_manager.inspect_export_table_references()
