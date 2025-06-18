import logging
from llama_index.core.workflow import Context, step
from llama_index.core.llms import LLM
from llama_index.core.indices.struct_store.sql_query import DEFAULT_RESPONSE_SYNTHESIS_PROMPT
from llama_index.core.prompts import PromptTemplate
from oso_agent.workflows.base import MixableWorkflow, ResourceDependency
from oso_agent.workflows.types import (
    Text2SQLGenerationEvent,
    SQLResultEvent,
    SQLResultSummaryRequestEvent,
    SQLResultSummaryResponseEvent,
)
from pyoso import Client
from ..tool.oso_mcp_client import OsoMcpClient

logger = logging.getLogger(__name__)

class PyosoWorkflow(MixableWorkflow):
    """Mixin class to enable PyOSO integration for agent workflows."""

    oso_client: ResourceDependency[Client]

    @step
    async def retrieve_sql_results(
        self, ctx: Context, query: Text2SQLGenerationEvent
    ) -> SQLResultEvent:
        """Retrieve SQL results using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        try:
            return await self.execute_query(query.output_sql, query.id)
        except Exception as e:
            logger.error(f"Error retrieving SQL results: {e}")

            return SQLResultEvent(
                id=query.id,
                input_text=query.input_text,
                output_sql=query.output_sql,
                results=[],
                error=e,
            )

    async def execute_query(
        self, query: str, id: str = "query_execution"
    ) -> SQLResultEvent:
        """Execute a SQL query using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of executing a query and returning results
        df = self.oso_client.to_pandas(query)

        return SQLResultEvent(
            id=id,
            input_text=query,
            output_sql=query,
            results=df,
        )

    
class McpDBWorkflow(MixableWorkflow):
    """Mixin class to enable a soon to be deprecated integration for accessing the DB via the MCP"""

    oso_mcp_client: ResourceDependency[OsoMcpClient]

    @step
    async def retrieve_sql_results(
        self, ctx: Context, query: Text2SQLGenerationEvent
    ) -> SQLResultEvent:
        """Retrieve SQL results using the MCP DB client."""
        if not self.oso_mcp_client:
            raise ValueError("MCP DB client is not initialized.")
        
        try:
            return await self.execute_query(query.output_sql, query.id)
        except Exception as e:
            logger.error(f"Error retrieving SQL results: {e}")

            return SQLResultEvent(
                id=query.id,
                input_text=query.input_text,
                output_sql=query.output_sql,
                results=[],
                error=e,
            )

    async def execute_query(
        self, query: str, id: str = "query_execution"
    ) -> SQLResultEvent:
        """Execute a SQL query using the PyOSO client."""
        if not self.oso_mcp_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of executing a query and returning results
        results = await self.oso_mcp_client.query_oso(query)

        return SQLResultEvent(
            id=id,
            input_text=query,
            output_sql=query,
            results=results,
        )

class SQLRowsResponseSynthesisMixin(MixableWorkflow):
    """Mixin class to enable SQL response synthesis in agent workflows."""

    response_synthesis_prompt: ResourceDependency[PromptTemplate] = ResourceDependency(
        default_factory=lambda: DEFAULT_RESPONSE_SYNTHESIS_PROMPT
    )
    llm: ResourceDependency[LLM]

    # @step
    # async def synthesize_sql_response_from_dataframes(
    #     self, ctx: Context, request: SQLDataFrameResultSummaryRequestEvent
    # ) -> SQLDataFrameResultSummaryResponseEvent:
    #     """Synthesize a SQL response from the generated SQL query."""

    #     # TODO add actual synthesis logic here
    #     response = self.llm.predict(
    #         self.response_synthesis_prompt,
    #         query_str=request.result.input_text,
    #         sql_query=request.result.output_sql,
    #         sql_response_str=str(request.result.df)
    #     )

    #     return SQLDataFrameResultSummaryResponseEvent(
    #         summary=response,
    #         result=request.result,
    #     )
    
    @step
    async def synthesize_sql_response_from_rows(
        self, request: SQLResultSummaryRequestEvent
    ) -> SQLResultSummaryResponseEvent:
        """Synthesize a SQL response from the generated SQL query and rows."""

        response = self.llm.predict(
            self.response_synthesis_prompt,
            query_str=request.result.input_text,
            sql_query=request.result.output_sql,
            sql_response_str=request.result.result_to_str(),
        )

        return SQLResultSummaryResponseEvent(
            id=request.id,
            summary=response,
            result=request.result,
        )