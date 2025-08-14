import hashlib
import logging

from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.workflow import Context, StopEvent, step
from oso_agent.types.response import StrResponse
from oso_agent.workflows.types import (
    RetrySemanticQueryEvent,
    SQLResultSummaryResponseEvent,
    StartQueryEngineEvent,
)

from ...resources import ResourceDependency
from ..base import StartingWorkflow
from .events import Text2SQLStartEvent
from .mixins import (
    GenericText2SQLRouter,
    OsoDBWorkflow,
    OsoQueryEngineWorkflowMixin,
    SQLRowsResponseSynthesisMixin,
)

logger = logging.getLogger(__name__)


class BasicText2SQL(
    StartingWorkflow[Text2SQLStartEvent],
    GenericText2SQLRouter,
    OsoDBWorkflow,
    SQLRowsResponseSynthesisMixin,
    OsoQueryEngineWorkflowMixin,
):
    """The basic text to sql agent that just uses the descriptions and a rag to
    retrieve row context
    """

    llm: ResourceDependency[FunctionCallingLLM]
    max_retries: int = 5

    @step
    async def handle_text2sql_query(
        self, _ctx: Context, event: Text2SQLStartEvent
    ) -> StartQueryEngineEvent:
        """Handle the start event by initiating the QueryEngine workflow."""

        if not event.id:
            # Generate a unique ID for the event if not provided
            event.id = hashlib.sha1(event.input.encode()).hexdigest()
            logger.debug("No ID provided for event, generated ID: %s", event.id)

        logger.info(
            "Handling text2sql query with input query[%s]: %s",
            event.id,
            event.input,
        )

        return StartQueryEngineEvent(
            id=event.id,
            input_text=event.input,
            synthesize_response=event.synthesize_response,
            execute_sql=event.execute_sql,
        )

    @step
    async def return_response(
        self, response: SQLResultSummaryResponseEvent
    ) -> StopEvent:
        """Return the response from the SQL query."""
        logger.debug(
            "Returning response for query[%s] with summary: %s",
            response.id,
            response.summary,
        )

        return StopEvent(result=StrResponse(blob=response.summary))

    # TODO(jabolo): We may want to rename `RetrySemanticQueryEvent` to
    # `RetryEvent` to make it more generic in the future.
    @step
    async def handle_retry_semantic_query(
        self, event: RetrySemanticQueryEvent
    ) -> StopEvent:
        """Handle retry events by raising an error"""
        error_msg = (
            f"Retries are not supported in BasicText2SQL workflow. "
            f"Original error: {event.error}. "
            f"Use SemanticText2SQLWorkflow for retry functionality."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
