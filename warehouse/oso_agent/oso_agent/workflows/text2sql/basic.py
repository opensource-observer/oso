import hashlib
import logging

from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.llms import LLM
from llama_index.core.tools import QueryEngineTool
from llama_index.core.workflow import Context, StartEvent, StopEvent, step
from oso_agent.types.response import StrResponse
from oso_agent.workflows.types import (
    SQLResultEvent,
    SQLResultSummaryRequestEvent,
    SQLResultSummaryResponseEvent,
    Text2SQLGenerationEvent,
)

from ...resources import ResourceDependency
from .mixins import McpDBWorkflow, SQLRowsResponseSynthesisMixin

logger = logging.getLogger(__name__)

class BasicText2SQL(McpDBWorkflow, SQLRowsResponseSynthesisMixin):
    """The basic text to sql agent that just uses the descriptions and a rag to
    retrieve row context
    """

    query_engine_tool: ResourceDependency[QueryEngineTool]
    llm: ResourceDependency[LLM]

    @step
    async def handle_text2sql_query(self, ctx: Context, event: StartEvent) -> Text2SQLGenerationEvent:
        """Handle the start event of the workflow."""
        # Here you would typically initialize the workflow, set up context, etc.
        # For this basic example, we just return a StopEvent to end the workflow.

        event_input_id = getattr(event, "id", "")
        if not event_input_id:
            # Generate a unique ID for the event if not provided
            event_input_id = hashlib.sha1(event.input.encode()).hexdigest()
            logger.debug(f"No ID provided for event, generated ID: {event_input_id}") 

        logger.info(f"Handling text2sql query with input query[{event_input_id}]: {event.input}")

        try:
            tool_output = await self.query_engine_tool.acall(
                input=event.input,
                context=ctx,
            )
            logger.debug(f"query engine called successfully for query[{event_input_id}]")
        except Exception as e:
            logger.error(f"Error calling query engine tool query[{event_input_id}]: {e}")
            raise ValueError(f"Failed to call query engine tool query[{event_input_id}]: {e}")

        raw_output = tool_output.raw_output
        assert isinstance(raw_output, ToolResponse), "Expected a ToolResponse from the query engine tool"

        if raw_output.metadata is None:
            raise ValueError("No metadata in query engine tool output")

        output_sql = raw_output.metadata.get("sql_query")

        logger.debug(f"query engine tool created the following SQL query for query[{event_input_id}]: {output_sql}")
        if not output_sql:
            raise ValueError("No SQL query found in metadata of query engine tool output")

        return Text2SQLGenerationEvent(
            id=event_input_id,
            output_sql=output_sql,
            input_text=event.input,
        )
    
    @step
    async def handle_sql_results_rows(self, result: SQLResultEvent) -> SQLResultSummaryRequestEvent:
        """Handle the SQL results routing to request a synthesized response."""
        # Here you can process the rows as needed, for example, summarizing them.
        # For this basic example, we just return the rows as a summary.

        logger.info(f"Handling SQL results for query[{result.id}] with {len(result.results)} rows")

        return SQLResultSummaryRequestEvent(
            id=result.id,
            result=result
        )

    @step
    async def return_response(self, response: SQLResultSummaryResponseEvent) -> StopEvent:
        """Return the response from the SQL query."""
        # This step can be used to process the response further or just return it.

        logger.debug(f"Returning response for query[{response.id}] with summary: {response.summary}")

        return StopEvent(
            result=StrResponse(blob=response.summary)
        )

