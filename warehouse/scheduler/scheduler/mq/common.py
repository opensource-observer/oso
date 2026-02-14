"""
Implementations of the run context and step context for message handlers.
"""

import typing as t
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from aioprometheus.collectors import Counter, Histogram
from google.protobuf.message import Message as ProtobufMessage
from oso_core.instrumentation import MetricsContainer
from oso_core.instrumentation.common import MetricsLabeler
from oso_core.instrumentation.timing import async_time
from oso_core.resources import ResourcesContext
from oso_dagster.resources.gcs import GCSFileResource
from posthog import Posthog
from scheduler.config import CommonSettings
from scheduler.graphql_client.client import UNSET
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.graphql_client.create_materialization import CreateMaterialization
from scheduler.graphql_client.enums import RunStatus, StepStatus
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
from scheduler.logging import (
    BindableLogger,
    BufferedLogger,
    GCSLogBuffer,
    ProxiedBoundLogger,
)
from scheduler.types import (
    AlreadyLockedMessageResponse,
    FailedResponse,
    HandlerResponse,
    MaterializationStrategy,
    MessageHandler,
    RunContext,
    RunContextView,
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
        materialization_strategy: MaterializationStrategy,
        metrics: MetricsContainer,
        gcs: "GCSFileResource",
        gcs_bucket: str,
        internal_logger: BindableLogger,
    ) -> "OSORunContext":
        gcs_client = gcs.get_client(asynchronous=True)
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")

        log_destination_path = (
            f"{gcs_bucket}/run-logs/{date_prefix}/{run_id}/logs.jsonl"
        )
        log_buffer = GCSLogBuffer(
            run_id=run_id,
            destination_path=log_destination_path,
            gcs_client=gcs_client,
        )

        buffered_logger = BufferedLogger(log_buffer, context={"run_id": run_id})
        proxied_logger = ProxiedBoundLogger([internal_logger, buffered_logger])
        get_run_data = await oso_client.get_run(run_id=run_id)
        run_data = get_run_data.runs.edges[0].node

        return cls(
            run_id,
            oso_client,
            run_data,
            materialization_strategy,
            proxied_logger,
            internal_logger,
            log_buffer,
            metrics,
        )

    def __init__(
        self,
        run_id: str,
        oso_client: OSOClient,
        run_data: RunCommon,
        materialization_strategy: MaterializationStrategy,
        logger: BindableLogger,
        internal_logger: BindableLogger,
        log_buffer: GCSLogBuffer,
        metrics: MetricsContainer,
    ) -> None:
        self._run_id = run_id
        self._oso_client = oso_client
        self._run_data = run_data
        self._materialization_strategy = materialization_strategy
        self._logger = logger
        self._internal_logger = internal_logger
        self._log_buffer = log_buffer
        self._metrics = metrics

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
            await self._log_buffer.flush()
        except Exception as e:
            self.internal_log.error(
                f"Failed to upload logs to GCS for run_id {self._run_id}: {e}",
                exc_info=True,
            )

        return await self._oso_client.finish_run(
            run_id=self._run_id,
            status=status,
            status_code=status_code,
            logs_url=self._log_buffer.destination_url,
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
        gcs: GCSFileResource,
    ) -> HandlerResponse:
        run_id = getattr(message, "run_id", None)
        if not run_id:
            logger.error(
                "Message does not contain a run_id; acknowledging and skipping."
            )
            return SkipResponse()
        if not isinstance(run_id, bytes):
            logger.error("run_id is not of type bytes; acknowledging and skipping.")
            return SkipResponse()

        run_id_str = convert_uuid_bytes_to_str(run_id)

        async with async_time(
            metrics.histogram("run_context_load_duration_ms")
        ) as labeler_ctx:
            run_context = await OSORunContext.create(
                oso_client,
                run_id=run_id_str,
                materialization_strategy=materialization_strategy,
                metrics=metrics,
                gcs=gcs,
                gcs_bucket=common_settings.run_logs_gcs_bucket,
                internal_logger=logger.bind(run_id=run_id_str),
            )
            labeler_ctx.add_labels({"org_id": run_context.organization.name})

        posthog_client.capture(
            "run_message_received",
            properties={
                "run_id": run_id_str,
                "org_name": run_context.organization.name,
                "trigger_type": run_context.trigger_type,
                "requested_by": run_context.requested_by.email
                if run_context.requested_by
                else "unknown",
            },
        )

        labeler = MetricsLabeler()
        # Try to set the run to running in the database for user's visibility
        try:
            run_context.log.info(f"Reporting run {run_id_str} as started.")
            await oso_client.start_run(run_id=run_id_str)
        except Exception as e:
            logger.error(f"Error starting run {run_id_str}: {e}")

            labeler.set_labels(
                {
                    "org_id": "unknown",
                    "trigger_type": "unknown",
                }
            )

            return await self.report_response(
                run_id_str=run_id_str,
                run_context=run_context,
                response=FailedResponse(message=f"Failed to start run {run_id_str}."),
                metrics=metrics,
                labeler=labeler,
                posthog_client=posthog_client,
                logger=logger,
            )

        labeler.set_labels(
            {
                "org_id": run_context.organization.name,
                "trigger_type": run_context.trigger_type,
            }
        )
        try:
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
        except Exception as e:
            logger.error(f"Error handling run message for run_id {run_id_str}: {e}")
            response = FailedResponse(
                exception=e,
                message=f"Failed to process the message for run_id {run_id_str}.",
            )

        try:
            return await self.report_response(
                run_id_str=run_id_str,
                response=response,
                run_context=run_context,
                metrics=metrics,
                labeler=labeler,
                posthog_client=posthog_client,
                logger=logger,
            )
        except Exception as e:
            logger.error(f"Error reporting response for run_id {run_id_str}: {e}")

            return FailedResponse(
                exception=e,
                message=f"Failed to report the response for run_id {run_id_str}.",
            )

    async def report_response(
        self,
        run_id_str: str,
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
            "run_id": run_id_str,
            "org_name": run_context.organization.name,
            "trigger_type": run_context.trigger_type,
            "response_type": type(response).__name__,
            "requested_by": run_context.requested_by.email
            if run_context.requested_by
            else "unknown",
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
                logger.error(f"Failed to process run_id {run_id_str}.")
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
                logger.info(f"Successfully processed run_id {run_id_str}.")
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
                    f"Unhandled response type {type(response)} from run message handler for run_id {run_id_str}."
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
