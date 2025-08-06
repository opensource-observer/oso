import hashlib
import logging

from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.workflow import Context, StartEvent, StopEvent, step
from oso_agent.types.response import StrResponse
from oso_agent.workflows.types import (
    RetrySemanticQueryEvent,
    SQLResultSummaryResponseEvent,
    StartQueryEngineEvent,
)

from ...resources import ResourceDependency
from .mixins import (
    GenericText2SQLRouter,
    OsoDBWorkflow,
    OsoQueryEngineWorkflowMixin,
    SQLRowsResponseSynthesisMixin,
)

logger = logging.getLogger(__name__)


class BasicText2SQL(
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
        self, _ctx: Context, event: StartEvent
    ) -> StartQueryEngineEvent:
        """Handle the start event by initiating the QueryEngine workflow."""
        event_input_id = getattr(event, "id", "")

        if not event_input_id:
            # Generate a unique ID for the event if not provided
            event_input_id = hashlib.sha1(event.input.encode()).hexdigest()
            logger.debug("No ID provided for event, generated ID: %s", event_input_id)

        logger.info(
            "Handling text2sql query with input query[%s]: %s",
            event_input_id,
            event.input,
        )

        synthesize_response = bool(getattr(event, "synthesize_response", True))
        execute_sql = bool(getattr(event, "execute_sql", True))

        return StartQueryEngineEvent(
            id=event_input_id,
            input_text=event.input,
            synthesize_response=synthesize_response,
            execute_sql=execute_sql,
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
