from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.tools import QueryEngineTool
from llama_index.core.workflow import Context, StartEvent, step
from oso_agent.workflows.types import Text2SQLGenerationEvent

from ..base import ResourceDependency
from ..mixins import PyosoWorkflow, SQLResponseSynthesisMixin


class BasicText2SQL(PyosoWorkflow, SQLResponseSynthesisMixin):
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

        assert isinstance(tool_output, ToolResponse), "Expected a ToolResponse from the query engine tool"

        return Text2SQLGenerationEvent(
            generated_sql=tool_output.raw_output,
            text_input=event.text,
        )
        

