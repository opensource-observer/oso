from llama_index.core.workflow import Context, step
from oso_agent.workflows.base import MixableWorkflow, ResourceDependency
from oso_agent.workflows.types import (
    SQLDataFrameResultEvent,
    SQLDataFrameResultSummaryRequestEvent,
    SQLDataFrameResultSummaryResponseEvent,
    Text2SQLGenerationEvent,
)
from pyoso import Client


class PyosoWorkflow(MixableWorkflow):
    """Mixin class to enable PyOSO integration for agent workflows."""

    oso_client: ResourceDependency[Client]

    @step
    def retrieve_sql_results(
        self, ctx: Context, query: Text2SQLGenerationEvent
    ) -> SQLDataFrameResultEvent:
        """Retrieve SQL results using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of using the PyOSO client to execute a query
        df = self.oso_client.to_pandas(query.generated_sql)

        return SQLDataFrameResultEvent(
            sql_query=query.generated_sql,
            result=df,
        )


class SQLResponseSynthesisMixin(MixableWorkflow):
    """Mixin class to enable SQL response synthesis in agent workflows."""

    response_synthesis_prompt: ResourceDependency[str]

    @step
    async def synthesize_sql_response(
        self, ctx: Context, query: SQLDataFrameResultSummaryRequestEvent
    ) -> SQLDataFrameResultSummaryResponseEvent:
        """Synthesize a SQL response from the generated SQL query."""

        # TODO add actual synthesis logic here
        

        return SQLDataFrameResultSummaryResponseEvent(
            summary=query.prompt,
            result=query.result,
        )
    