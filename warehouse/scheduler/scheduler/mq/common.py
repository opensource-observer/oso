"""
Implementations of the run context and step context for message handlers.
"""

import asyncio
import typing as t
import uuid
from contextlib import asynccontextmanager

from aioprometheus.collectors import Counter, Histogram
from google.protobuf.message import Message as ProtobufMessage
from oso_core.instrumentation import MetricsContainer
from oso_core.instrumentation.common import MetricsLabeler
from oso_core.instrumentation.timing import async_time
from oso_core.logging import (
    BindableLogger,
    ProxiedBoundLogger,
)
from oso_core.resources import ResourcesContext
from posthog import Posthog
from scheduler.config import CommonSettings
from scheduler.graphql_client.client import UNSET
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.graphql_client.create_materialization import CreateMaterialization
from scheduler.graphql_client.enums import RunStatus, StepStatus
from scheduler.graphql_client.exceptions import (
    GraphQLClientGraphQLError,
    GraphQLClientGraphQLMultiError,
)
from scheduler.graphql_client.finish_run import FinishRun
from scheduler.graphql_client.fragments import (
    DatasetCommon,
    OrganizationCommon,
    RunCommon,
    UserCommon,
)
from scheduler.graphql_client.input_types import (
    DataModelColumnInput,
    UpdateMetadataInput,
)
from scheduler.graphql_client.update_run_metadata import UpdateRunMetadata
from scheduler.types import (
    AlreadyLockedMessageResponse,
    ConcurrencyLockStore,
    FailedResponse,
    HandlerResponse,
    MaterializationStrategy,
    MessageHandler,
    RunContext,
    RunContextView,
    RunLoggerContainer,
    RunLoggerFactory,
    SkipResponse,
    StepContext,
    StepFailedException,
    SuccessResponse,
)
from scheduler.utils import convert_uuid_bytes_to_str

T = t.TypeVar("T", bound=ProtobufMessage)


class OSOStepContext(StepContext):
    @classmethod
    def create(
        cls,
        run: RunContextView,
        step_id: str,
        oso_client: OSOClient,
        materialization_strategy: MaterializationStrategy,
        logger: BindableLogger,
        internal_logger: BindableLogger,
    ) -> "OSOStepContext":
        return cls(
            run, step_id, oso_client, materialization_strategy, logger, internal_logger
        )

    def __init__(
        self,
        run: RunContextView,
        step_id: str,
        oso_client: OSOClient,
        materialization_strategy: MaterializationStrategy,
        logger: BindableLogger,
        internal_logger: BindableLogger,
    ) -> None:
        self._run = run
        self._step_id = step_id
        self._oso_client = oso_client
        self._materialization_strategy = materialization_strategy
        self._logger = logger
        self._internal_logger = internal_logger

    @property
    def log(self) -> BindableLogger:
        return self._logger

    @property
    def internal_log(self) -> BindableLogger:
        return self._internal_logger

    @property
    def materialization_strategy(self) -> MaterializationStrategy:
        return self._materialization_strategy

    async def create_materialization(
        self, table_id: str, warehouse_fqn: str, schema: list[DataModelColumnInput]
    ) -> CreateMaterialization:
        self._logger.debug("Creating materialization")
        # Placeholder for actual materialization creation logic

        return await self._oso_client.create_materialization(
            step_id=self._step_id,
            table_id=table_id,
            warehouse_fqn=warehouse_fqn,
            schema=schema,
        )

    @property
    def step_id(self) -> str:
        return self._step_id

    @property
    def run(self) -> RunContextView:
        return self._run


class OSORunContext(RunContext):
    @classmethod
    async def create(
        cls,
        oso_client: OSOClient,
        run_id: str,
        internal_processing_id: str,
        materialization_strategy: MaterializationStrategy,
        metrics: MetricsContainer,
        internal_logger: BindableLogger,
        run_logger_factory: RunLoggerFactory,
    ) -> "OSORunContext":
        logging_context = internal_logger._context
        logging_context.pop("run_id", None)
        run_logger_container = run_logger_factory.create_logger_container(
            run_id, **logging_context
        )
        proxied_logger = ProxiedBoundLogger(
            [internal_logger, run_logger_container.logger]
        )
        get_run_data = await oso_client.get_run(run_id=run_id)
        run_data = get_run_data.runs.edges[0].node

        return cls(
            run_id=run_id,
            internal_processing_id=internal_processing_id,
            oso_client=oso_client,
            run_data=run_data,
            materialization_strategy=materialization_strategy,
            logger=proxied_logger,
            internal_logger=internal_logger,
            metrics=metrics,
            run_logger_container=run_logger_container,
        )

    def __init__(
        self,
        run_id: str,
        internal_processing_id: str,
        oso_client: OSOClient,
        run_data: RunCommon,
        materialization_strategy: MaterializationStrategy,
        logger: BindableLogger,
        internal_logger: BindableLogger,
        metrics: MetricsContainer,
        run_logger_container: RunLoggerContainer,
    ) -> None:
        self._run_id = run_id
        self._internal_processing_id = internal_processing_id
        self._oso_client = oso_client
        self._run_data = run_data
        self._materialization_strategy = materialization_strategy
        self._logger = logger
        self._internal_logger = internal_logger
        self._metrics = metrics
        self._run_logger_container = run_logger_container

    @property
    def log(self) -> BindableLogger:
        return self._logger

    @property
    def internal_log(self) -> BindableLogger:
        return self._internal_logger

    @property
    def materialization_strategy(self) -> MaterializationStrategy:
        return self._materialization_strategy

    async def update_metadata(
        self, metadata: dict[str, t.Any], merge: bool
    ) -> UpdateRunMetadata:
        """Updates the run metadata for the current run."""
        self._logger.info("Updating run metadata")
        # Placeholder for actual metadata update logic
        return await self._oso_client.update_run_metadata(
            run_id=self._run_id,
            metadata=UpdateMetadataInput(value=metadata, merge=merge),
        )

    @asynccontextmanager
    async def step_context(
        self, name: str, display_name: str
    ) -> t.AsyncIterator[StepContext]:
        # Create the new step
        step = await self._oso_client.start_step(
            name=name, run_id=self._run_id, display_name=display_name
        )
        step = step.start_step.step

        try:
            async with async_time(self._metrics.histogram("step_duration_ms")):
                step_context = OSOStepContext.create(
                    run=self.as_view,
                    step_id=step.id,
                    oso_client=self._oso_client,
                    materialization_strategy=self._materialization_strategy,
                    logger=self._logger.bind(
                        step_id=step.id, step=name, step_display_name=display_name
                    ),
                    internal_logger=self._internal_logger.bind(
                        step_id=step.id, step=name, step_display_name=display_name
                    ),
                )
                step_context.log.debug(f"Started step {name} with ID: {step.id}")
                yield step_context
        except Exception as e:
            self._logger.error(f"Error in step context {name}: {e}")
            await self._oso_client.finish_step(
                step_id=step.id,
                status=StepStatus.FAILED,
                logs_url="https://example.com/logs",
            )
            # Re-raise the exception to propagate it to the run level
            raise StepFailedException(inner_exception=e)
        else:
            await self._oso_client.finish_step(
                step_id=step.id,
                status=StepStatus.SUCCESS,
                logs_url="https://example.com/logs",
            )

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def organization(self) -> OrganizationCommon:
        return self._run_data.organization

    @property
    def dataset(self) -> t.Optional[DatasetCommon]:
        return self._run_data.dataset

    @property
    def requested_by(self) -> t.Optional[UserCommon]:
        return self._run_data.requested_by

    @property
    def trigger_type(self) -> str:
        return self._run_data.trigger_type

    async def finish_run(
        self,
        status: RunStatus,
        status_code: int,
        metadata: UpdateMetadataInput | None = None,
    ) -> FinishRun:
        """Finish the run with the given status."""
        self.log.info(
            f"Finishing run with status: {status}, status_code: {status_code}"
        )

        try:
            destination_uris = await self._run_logger_container.destination_uris()
        except Exception as e:
            self.internal_log.error(
                f"Failed to upload logs to GCS for run_id {self._run_id}: {e}",
                exc_info=True,
            )
            destination_uris = []  # Fallback logs URL

        return await self._oso_client.finish_run(
            run_id=self._run_id,
            status=status,
            status_code=status_code,
            logs_url=destination_uris[0]
            if destination_uris
            else "https://example.com/logs",
            metadata=metadata if metadata else UNSET,
        )


class RunHandler(MessageHandler[T]):
    """A message handler that processes run messages."""

    def initialize(self, metrics: MetricsContainer) -> None:
        super().initialize(metrics=metrics)

        metrics.initialize_histogram(
            Histogram("run_context_load_duration_ms", "Duration to load run context"),
        )

        metrics.initialize_histogram(
            Histogram(
                "run_message_handling_duration_ms",
                "Duration to handle run message (specifically for `handle_run_message` duration)",
            ),
        )

        metrics.initialize_counter(
            Counter(
                "run_count_total",
                "Total number of run requests processed",
            )
        )

        metrics.initialize_histogram(
            Histogram("step_duration_ms", "Duration of each step in the run"),
        )

    async def handle_message(
        self,
        message: ProtobufMessage,
        logger: BindableLogger,
        resources: ResourcesContext,
        materialization_strategy: MaterializationStrategy,
        metrics: MetricsContainer,
        posthog_client: Posthog,
        oso_client: OSOClient,
        common_settings: CommonSettings,
        concurrency_lock_store: ConcurrencyLockStore,
        run_logger_factory: RunLoggerFactory,
    ) -> HandlerResponse:
        run_id_bytes = getattr(message, "run_id", None)
        internal_processing_id = str(uuid.uuid4())

        # A bit of a hack to bind the internal processing id to the current
        # logger by mutating the passed in logger. This is because we can't
        # actually extract the context from a BindableLogger.
        logger = logger.bind(internal_processing_id=internal_processing_id)

        if not run_id_bytes:
            logger.error(
                "Message does not contain a run_id; acknowledging and skipping."
            )
            return SkipResponse()
        if not isinstance(run_id_bytes, bytes):
            logger.error("run_id is not of type bytes; acknowledging and skipping.")
            return SkipResponse()

        run_id = convert_uuid_bytes_to_str(run_id_bytes)

        async with self.worker_run_lock(
            run_id, concurrency_lock_store, logger, common_settings
        ) as (lock_acquired, renew_task):
            if not lock_acquired:
                logger.warning(
                    f"Run ID {run_id} is already being processed by another worker. Skipping.",
                )
                return AlreadyLockedMessageResponse()

            message_handling_task = asyncio.create_task(
                self._handle_run_message(
                    message=message,
                    logger=logger,
                    resources=resources,
                    materialization_strategy=materialization_strategy,
                    metrics=metrics,
                    posthog_client=posthog_client,
                    oso_client=oso_client,
                    run_logger_factory=run_logger_factory,
                    run_id=run_id,
                    internal_processing_id=internal_processing_id,
                )
            )
            try:
                done, pending = await asyncio.wait(
                    [message_handling_task, renew_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=common_settings.message_handling_timeout_seconds,
                )
            except asyncio.CancelledError:
                logger.warning(
                    "Message handling was cancelled. Cancelling the message handling task and renewal task."
                )
                message_handling_task.cancel()
                renew_task.cancel()
                return await message_handling_task
            if message_handling_task in pending:
                logger.error(
                    f"Message processing task did not complete within the timeout of {common_settings.message_handling_timeout_seconds} seconds. Cancelling the task."
                )
                message_handling_task.cancel()
                return FailedResponse(message="Message processing timed out.")
            if renew_task in done:
                logger.error(
                    "Fatal: Auto concurrency lock renewal task completed before message handling task. This should not happen as the renew task is supposed to run indefinitely until cancelled. An unexpected issue occurred."
                )
                # We can continue processing the message, but we should log this as it may indicate an issue with the concurrency lock store.
                raise RuntimeError(
                    "Concurrency lock renewal task completed unexpectedly."
                )

            return await message_handling_task

    @asynccontextmanager
    async def worker_run_lock(
        self,
        run_id: str,
        concurrency_lock_store: ConcurrencyLockStore,
        logger: BindableLogger,
        common_settings: CommonSettings,
    ) -> t.AsyncIterator[t.Tuple[bool, asyncio.Task]]:
        """Context manager that acquires a lock for the given run_id and releases it after the block is done."""

        async def renew_lock_periodically():
            while True:
                await asyncio.sleep(common_settings.concurrency_lock_ttl_seconds / 4.0)
                renewed = await concurrency_lock_store.renew_lock(
                    run_id,
                    ttl_seconds=common_settings.concurrency_lock_ttl_seconds,
                    log_override=logger,
                )
                if not renewed:
                    logger.warning(
                        f"Failed to renew lock for run ID {run_id}. Another worker may have taken over processing. Stopping processing of this message.",
                    )
                    break

        lock_acquired = await concurrency_lock_store.acquire_lock(
            run_id,
            ttl_seconds=common_settings.concurrency_lock_ttl_seconds,
            log_override=logger,
        )
        renew_task = asyncio.create_task(renew_lock_periodically())
        try:
            yield lock_acquired, renew_task
        finally:
            renew_task.cancel()
            try:
                async with asyncio.timeout(1):
                    await renew_task
            except asyncio.CancelledError:
                # Fully expected, but we set a timeout just in case to avoid any
                # potential hangs. Log just in case it takes longer than
                # expected.
                pass
            except asyncio.TimeoutError:
                logger.error(
                    "Cancellation of renewal task timed out, it may still be running in the background."
                )

            # We always renew the lock to half the normal ttl at the end to
            # ensure that any potential post processing or eventual consistency
            # is covered by the lock.
            await concurrency_lock_store.renew_lock(
                run_id,
                ttl_seconds=int(common_settings.concurrency_lock_ttl_seconds / 2),
                log_override=logger,
            )

    async def _handle_run_message(
        self,
        message: ProtobufMessage,
        logger: BindableLogger,
        resources: ResourcesContext,
        materialization_strategy: MaterializationStrategy,
        metrics: MetricsContainer,
        posthog_client: Posthog,
        oso_client: OSOClient,
        run_logger_factory: RunLoggerFactory,
        run_id: str,
        internal_processing_id: str,
    ) -> HandlerResponse:
        internal_logger = logger.bind(
            run_id=run_id, internal_processing_id=internal_processing_id
        )
        async with async_time(
            metrics.histogram("run_context_load_duration_ms")
        ) as labeler_ctx:
            run_context = await OSORunContext.create(
                oso_client,
                run_id=run_id,
                internal_processing_id=internal_processing_id,
                materialization_strategy=materialization_strategy,
                metrics=metrics,
                run_logger_factory=run_logger_factory,
                internal_logger=internal_logger,
            )
            labeler_ctx.add_labels({"org_id": run_context.organization.name})

        posthog_client.capture(
            "run_message_received",
            properties={
                "run_id": run_id,
                "org_name": run_context.organization.name,
                "trigger_type": run_context.trigger_type,
                "requested_by": (
                    run_context.requested_by.email
                    if run_context.requested_by
                    else "unknown"
                ),
            },
        )

        labeler = MetricsLabeler()
        # Try to set the run to running in the database for user's visibility
        try:
            run_context.log.info(f"Reporting run {run_id} as started.")
            await oso_client.start_run(run_id=run_id)
        except Exception as e:
            run_context.log.error(
                f"Error starting run {run_id}", exc_info=True, exception=e
            )

            labeler.set_labels(
                {
                    "org_id": "unknown",
                    "trigger_type": "unknown",
                }
            )

            return await self.report_response(
                run_id=run_id,
                run_context=run_context,
                response=FailedResponse(message=f"Failed to start run {run_id}."),
                metrics=metrics,
                labeler=labeler,
                posthog_client=posthog_client,
                logger=internal_logger,
            )

        labeler.set_labels(
            {
                "org_id": run_context.organization.name,
                "trigger_type": run_context.trigger_type,
            }
        )
        response: HandlerResponse | None = None
        try:
            response = await self._execute_subclass_handle_run_message(
                metrics=metrics,
                resources=resources,
                message=message,
                run_context=run_context,
                logger=internal_logger,
                labeler=labeler,
            )
        except Exception as e:
            response = await self._convert_exception_into_response(e, internal_logger)
        except asyncio.CancelledError:
            response = FailedResponse(message="Run cancelled during message handling.")
        finally:
            if response is None:
                response = FailedResponse(
                    message="Run message handling completed without a response."
                )
            try:
                return await self.report_response(
                    run_id=run_id,
                    response=response,
                    run_context=run_context,
                    metrics=metrics,
                    labeler=labeler,
                    posthog_client=posthog_client,
                    logger=internal_logger,
                )
            except Exception as e:
                # This is a very exceptional case and we should likely alert if we
                # get this.
                internal_logger.error(
                    f"Fatal: Error reporting response for run_id {run_id}",
                    exc_info=True,
                    exception=e,
                )

                return FailedResponse(
                    exception=e,
                    message=f"Failed to report the response for run_id {run_id}.",
                )

    async def _convert_exception_into_response(
        self, exception: Exception, logger: BindableLogger
    ) -> FailedResponse:
        match exception:
            case GraphQLClientGraphQLMultiError(errors=errors):
                raw_errors = [
                    err.extensions.get("rawErrorMessage", err.message)
                    for err in errors
                    if err.extensions
                ]
                logger.error(
                    f"GraphQL errors: {raw_errors or [err.message for err in errors]}"
                )
                return FailedResponse(
                    exception=exception,
                    message="Failed to process the message due to GraphQL errors.",
                    details={
                        "graphql_errors": raw_errors or [err.message for err in errors]
                    },
                )
            case GraphQLClientGraphQLError(message=message, extensions=extensions):
                raw_error = (
                    extensions.get("rawErrorMessage", message)
                    if extensions
                    else message
                )
                logger.error(f"GraphQL error: {raw_error}")
                return FailedResponse(
                    exception=exception,
                    message="Failed to process the message due to a GraphQL error.",
                    details={"graphql_errors": [raw_error]},
                )
            case _:
                logger.error(f"Error: {exception}")
                return FailedResponse(
                    exception=exception,
                    message="Failed to process the message due to an unexpected error.",
                )

    async def _execute_subclass_handle_run_message(
        self,
        resources: ResourcesContext,
        message: ProtobufMessage,
        run_context: OSORunContext,
        logger: BindableLogger,
        labeler: MetricsLabeler,
        metrics: MetricsContainer,
    ) -> HandlerResponse:
        async with async_time(
            metrics.histogram("run_message_handling_duration_ms"), labeler
        ):
            response = await resources.run(
                self.handle_run_message,
                additional_inject={
                    "message": message,
                    "context": run_context,
                },
            )
            return response

    async def report_response(
        self,
        run_id: str,
        run_context: OSORunContext,
        response: HandlerResponse,
        metrics: MetricsContainer,
        labeler: MetricsLabeler,
        posthog_client: Posthog,
        logger: BindableLogger,
    ) -> HandlerResponse:
        """Handle the response from processing a run message.

        Args:
            response: The response from processing the run message.
        """
        # Write the response to the database

        posthog_properties = {
            "run_id": run_id,
            "org_name": run_context.organization.name,
            "trigger_type": run_context.trigger_type,
            "response_type": type(response).__name__,
            "requested_by": (
                run_context.requested_by.email
                if run_context.requested_by
                else "unknown"
            ),
            "status_code": getattr(response, "status_code", "unknown"),
        }
        match response:
            case AlreadyLockedMessageResponse():
                # No need to do anything here as another worker is processing it
                metrics.counter("run_count_total").inc(
                    labeler.get_labels({"response_type": "already_locked"}),
                )
                posthog_client.capture(
                    "run_message_already_locked", properties=posthog_properties
                )
                return response
            case SkipResponse(status_code=status_code):
                await run_context.finish_run(
                    status=RunStatus.CANCELED,
                    status_code=status_code,
                )
                metrics.counter("run_count_total").inc(
                    labeler.get_labels({"response_type": "skipped"}),
                )
                posthog_client.capture(
                    "run_message_skipped", properties=posthog_properties
                )
                return response

            case FailedResponse(
                exception=exception, status_code=status_code, details=details
            ):
                logger.error(f"Failed to process run_id {run_id}.")
                metrics.counter("run_count_total").inc(
                    labeler.get_labels({"response_type": "failed"}),
                )
                if exception:
                    posthog_client.capture_exception(
                        exception, properties=posthog_properties
                    )
                else:
                    posthog_client.capture(
                        "run_message_failed", properties=posthog_properties
                    )
                await run_context.finish_run(
                    status=RunStatus.FAILED,
                    status_code=status_code,
                    metadata=UpdateMetadataInput(
                        value={"errorDetails": details},
                        merge=True,
                    ),
                )
                return response
            case SuccessResponse(status_code=status_code):
                logger.info(f"Successfully processed run_id {run_id}.")
                metrics.counter("run_count_total").inc(
                    labeler.get_labels({"response_type": "success"}),
                )
                await run_context.finish_run(
                    status=RunStatus.SUCCESS,
                    status_code=status_code,
                )
                return response
            case _:
                logger.warning(
                    f"Unhandled response type {type(response)} from run message handler for run_id {run_id}."
                )
                metrics.counter("run_count_total").inc(
                    labeler.get_labels({"response_type": "unknown"}),
                )
                posthog_client.capture(
                    "run_message_unhandled_response", properties=posthog_properties
                )
                await run_context.finish_run(
                    status=RunStatus.FAILED,
                    status_code=500,
                )
                return FailedResponse(message="Unhandled response type.")

    async def handle_run_message(self, *args, **kwargs) -> HandlerResponse:
        raise NotImplementedError(
            "handle_run_message must be implemented by subclasses."
        )
