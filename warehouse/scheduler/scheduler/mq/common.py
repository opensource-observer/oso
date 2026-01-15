"""
Implementations of the run context and step context for message handlers.
"""

import logging
import typing as t
from contextlib import asynccontextmanager

import structlog
from google.protobuf.message import Message as ProtobufMessage
from oso_core.resources import ResourcesContext
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.graphql_client.create_materialization import CreateMaterialization
from scheduler.graphql_client.enums import RunStatus, StepStatus
from scheduler.graphql_client.input_types import (
    DataModelColumnInput,
    UpdateMetadataInput,
)
from scheduler.graphql_client.update_run_metadata import UpdateRunMetadata
from scheduler.types import (
    AlreadyLockedMessageResponse,
    FailedResponse,
    HandlerResponse,
    MaterializationStrategy,
    MessageHandler,
    RunContext,
    SkipResponse,
    StepContext,
    SuccessResponse,
)
from scheduler.utils import convert_uuid_bytes_to_str

logger = structlog.getLogger(__name__)

T = t.TypeVar("T", bound=ProtobufMessage)


class OSOStepContext(StepContext):
    @classmethod
    def create(
        cls,
        step_id: str,
        oso_client: OSOClient,
        materialization_strategy: MaterializationStrategy,
        logger: structlog.BoundLogger,
    ) -> "OSOStepContext":
        return cls(step_id, oso_client, materialization_strategy, logger)

    def __init__(
        self,
        step_id: str,
        oso_client: OSOClient,
        materialization_strategy: MaterializationStrategy,
        logger: structlog.BoundLogger,
    ) -> None:
        self._step_id = step_id
        self._oso_client = oso_client
        self._materialization_strategy = materialization_strategy
        self._logger = logger

    @property
    def log(self) -> logging.Logger:
        return t.cast(logging.Logger, self._logger)

    @property
    def materialization_strategy(self) -> MaterializationStrategy:
        return self._materialization_strategy

    async def create_materialization(
        self, table_id: str, warehouse_fqn: str, schema: list[DataModelColumnInput]
    ) -> CreateMaterialization:
        self._logger.info("Creating materialization")
        # Placeholder for actual materialization creation logic

        return await self._oso_client.create_materialization(
            step_id=self._step_id,
            table_id=table_id,
            warehouse_fqn=warehouse_fqn,
            schema=schema,
        )

    @property
    def step_id(self) -> str:
        return str(self._logger.bindings.get("step", "unknown_step"))


class OSORunContext(RunContext):
    @classmethod
    def create(
        cls,
        oso_client: OSOClient,
        run_id: str,
        materialization_strategy: MaterializationStrategy,
    ) -> "OSORunContext":
        logger = structlog.get_logger(run_id)
        return cls(run_id, oso_client, materialization_strategy, logger)

    def __init__(
        self,
        run_id: str,
        oso_client: OSOClient,
        materialization_strategy: MaterializationStrategy,
        logger: structlog.BoundLogger,
    ) -> None:
        self._run_id = run_id
        self._oso_client = oso_client
        self._materialization_strategy = materialization_strategy
        self._logger = logger

    @property
    def log(self) -> logging.Logger:
        return t.cast(logging.Logger, self._logger)

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
            yield OSOStepContext.create(
                step.id,
                self._oso_client,
                self._materialization_strategy,
                self._logger.bind(step=name, step_display_name=display_name),
            )
        except Exception as e:
            self._logger.error(f"Error in step context {name}: {e}")
            await self._oso_client.finish_step(
                step_id=step.id,
                status=StepStatus.FAILED,
                logs_url="https://example.com/logs",
            )
        else:
            await self._oso_client.finish_step(
                step_id=step.id,
                status=StepStatus.SUCCESS,
                logs_url="https://example.com/logs",
            )


class RunHandler(MessageHandler[T]):
    """A message handler that processes run messages."""

    async def handle_message(
        self,
        message: ProtobufMessage,
        resources: ResourcesContext,
        materialization_strategy: MaterializationStrategy,
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

        oso_client: OSOClient = resources.resolve("oso_client")

        run_context = OSORunContext.create(
            oso_client,
            run_id=run_id_str,
            materialization_strategy=materialization_strategy,
        )

        # Try to set the run to running in the database for user's visibility
        try:
            run_context.log.info(f"Reporting run {run_id_str} as started.")
            await oso_client.start_run(run_id=run_id_str)
        except Exception as e:
            logger.error(f"Error starting run {run_id_str}: {e}")
            return await self.report_response(
                oso_client=oso_client,
                run_id_str=run_id_str,
                response=FailedResponse(message=f"Failed to start run {run_id_str}."),
            )

        try:
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
                message=f"Failed to process the message for run_id {run_id_str}."
            )
        return await self.report_response(
            oso_client=oso_client,
            run_id_str=run_id_str,
            response=response,
        )

    async def report_response(
        self, oso_client: OSOClient, run_id_str: str, response: HandlerResponse
    ) -> HandlerResponse:
        """Handle the response from processing a run message.

        Args:
            response: The response from processing the run message.
        """
        # Write the response to the database
        match response:
            case AlreadyLockedMessageResponse():
                # No need to do anything here as another worker is processing it
                return response
            case SkipResponse(status_code=status_code):
                await oso_client.finish_run(
                    run_id=run_id_str,
                    status=RunStatus.CANCELED,
                    status_code=status_code,
                    logs_url="http://example.com/run_logs",
                )
                return response
            case FailedResponse(status_code=status_code, details=details):
                logger.error(f"Failed to process run_id {run_id_str}.")
                await oso_client.finish_run(
                    run_id=run_id_str,
                    status=RunStatus.FAILED,
                    status_code=status_code,
                    logs_url="http://example.com/run_logs",
                    metadata=UpdateMetadataInput(
                        value={"error_details": details},
                        merge=True,
                    ),
                )
                return response
            case SuccessResponse(status_code=status_code):
                logger.info(f"Successfully processed run_id {run_id_str}.")
                await oso_client.finish_run(
                    run_id=run_id_str,
                    status=RunStatus.SUCCESS,
                    status_code=status_code,
                    logs_url="http://example.com/run_logs",
                )
                return response
            case _:
                logger.warning(
                    f"Unhandled response type {type(response)} from run message handler for run_id {run_id_str}."
                )
                await oso_client.finish_run(
                    run_id=run_id_str,
                    status=RunStatus.FAILED,
                    status_code=500,
                    logs_url="http://example.com/run_logs",
                )
                return FailedResponse(message="Unhandled response type.")

    async def handle_run_message(self, *args, **kwargs) -> HandlerResponse:
        raise NotImplementedError(
            "handle_run_message must be implemented by subclasses."
        )
