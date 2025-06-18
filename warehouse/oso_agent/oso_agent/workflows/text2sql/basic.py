from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.tools import QueryEngineTool
from llama_index.core.workflow import Context, StartEvent, step, StopEvent
from oso_agent.types.response import StrResponse
from oso_agent.workflows.types import Text2SQLGenerationEvent, SQLResultSummaryResponseEvent, SQLResultEvent, SQLResultSummaryRequestEvent

from ..base import ResourceDependency
from ..mixins import McpDBWorkflow, SQLRowsResponseSynthesisMixin


class BasicText2SQL(McpDBWorkflow, SQLRowsResponseSynthesisMixin):
    """The basic text to sql agent that just uses the descriptions and a rag to
    retrieve row context
    """

    query_engine_tool: ResourceDependency[QueryEngineTool]

    @step
    async def handle_text2sql_query(self, ctx: Context, event: StartEvent) -> Text2SQLGenerationEvent:
        """Handle the start event of the workflow."""
        # Here you would typically initialize the workflow, set up context, etc.
        # For this basic example, we just return a StopEvent to end the workflow.

        tool_output = await self.query_engine_tool.acall(
            input=event.input,
            context=ctx,
        )

        raw_output = tool_output.raw_output
        assert isinstance(raw_output, ToolResponse), "Expected a ToolResponse from the query engine tool"

        if raw_output.metadata is None:
            raise ValueError("No metadata in query engine tool output")

        output_sql = raw_output.metadata.get("sql_query")
        if not output_sql:
            raise ValueError("No SQL query found in metadata of query engine tool output")

        text2sql_id = getattr(event, "id", "text2sql_event")
        return Text2SQLGenerationEvent(
            id=text2sql_id,
            output_sql=output_sql,
            input_text=event.input,
        )
    
    @step
    async def handle_sql_results_rows(self, result: SQLResultEvent) -> SQLResultSummaryRequestEvent:
        """Handle the SQL results routing to request a synthesized response."""
        # Here you can process the rows as needed, for example, summarizing them.
        # For this basic example, we just return the rows as a summary.
        return SQLResultSummaryRequestEvent(
            id=result.id,
            result=result
        )

    @step
    async def return_response(self, response: SQLResultSummaryResponseEvent) -> StopEvent:
        """Return the response from the SQL query."""
        # This step can be used to process the response further or just return it.
        return StopEvent(
            result=StrResponse(blob=response.summary)
        )

