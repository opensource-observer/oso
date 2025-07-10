import logging

from llama_index.core.indices.struct_store.sql_query import (
    DEFAULT_RESPONSE_SYNTHESIS_PROMPT,
)
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.workflow import Context, StopEvent, step
from oso_agent.types.response import AnyResponse, SqlResponse
from oso_agent.types.sql_query import SqlQuery
from oso_agent.workflows.types import (
    SQLExecutionRequestEvent,
    SQLResultEvent,
    SQLResultSummaryRequestEvent,
    SQLResultSummaryResponseEvent,
    Text2SQLGenerationEvent,
)
from pyoso import Client

from ...clients.oso_client import OsoClient
from ...resources import ResourceDependency
from ..base import MixableWorkflow

logger = logging.getLogger(__name__)


class GenericText2SQLRouter(MixableWorkflow):
    """A generic mixin class for handling text to sql events in text2sql
    workflows.

    The two events this handles are Text2SQLGenerationEvent and SQLResultEvent.

    In both cases this mixin provides a way to short-circuit the workflow
    depending on the options specified in the given events.

    For Text2SQLGenerationEvent:
        - If execute_sql is True, it returns a SQLExecutionRequestEvent.
        - If execute_sql is False, it returns a StopEvent with the generated SQL.

    For SQLResultEvent:
        - If synthesize_response is True, it returns a SQLResultSummaryRequestEvent.
        - If synthesize_response is False, it returns a StopEvent with the raw results.
    """

    @step
    async def handle_text2sql_generation_event(
        self, ctx: Context, event: Text2SQLGenerationEvent
    ) -> SQLExecutionRequestEvent | StopEvent:
        """Handle the text to SQL query event."""
        if event.execute_sql:
            logger.debug(
                f"query execution requested for query[{event.id}]: {event.output_sql}"
            )
            return SQLExecutionRequestEvent(
                id=event.id,
                input_text=event.input_text,
                output_sql=event.output_sql,
                synthesize_response=event.synthesize_response,
            )
        else:
            logger.debug(
                f"query execution not requested for query[{event.id}]: {event.output_sql}"
            )
            return StopEvent(result=SqlResponse(query=SqlQuery(query=event.output_sql)))

    @step
    async def handle_sql_results_rows(
        self, result: SQLResultEvent
    ) -> SQLResultSummaryRequestEvent | StopEvent:
        """Handle the SQL results routing to request a synthesized response."""
        # Here you can process the rows as needed, for example, summarizing them.
        # For this basic example, we just return the rows as a summary.

        logger.info(
            f"Handling SQL results for query[{result.id}] with {len(result.results)} rows"
        )

        if not result.synthesize_response:
            logger.debug(f"SQL result synthesis not requested for query[{result.id}]")
            # If synthesis is not requested, we return the result directly
            # FIXME: we should create new response objects for dataframes and or row lists
            return StopEvent(result=AnyResponse(raw=result.results))

        logger.debug(f"SQL result synthesis requested for query[{result.id}]")
        return SQLResultSummaryRequestEvent(id=result.id, result=result)


class PyosoWorkflow(MixableWorkflow):
    """Mixin class to enable PyOSO integration for agent workflows."""

    oso_client: ResourceDependency[Client]

    @step
    async def retrieve_sql_results(
        self, ctx: Context, query: SQLExecutionRequestEvent
    ) -> SQLResultEvent:
        """Retrieve SQL results using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        try:
            return await self.execute_query(
                query.output_sql, query.input_text, query.id, query.synthesize_response
            )
        except Exception as e:
            logger.error(f"Error retrieving SQL results: {e}")

            return SQLResultEvent(
                id=query.id,
                input_text=query.input_text,
                output_sql=query.output_sql,
                results=[],
                error=e,
                synthesize_response=query.synthesize_response,
            )

    async def execute_query(
        self, query: str, input_text: str, id: str = "query_execution", synthesize_response: bool = True
    ) -> SQLResultEvent:
        """Execute a SQL query using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of executing a query and returning results
        df = self.oso_client.to_pandas(query)

        return SQLResultEvent(
            id=id,
            input_text=input_text,
            output_sql=query,
            results=df,
            synthesize_response=synthesize_response,
        )


class OsoDBWorkflow(MixableWorkflow):
    """Mixin class to enable a soon to be deprecated integration for accessing the DB"""

    oso_client: ResourceDependency[OsoClient]

    @step
    async def retrieve_sql_results(
        self, ctx: Context, query: SQLExecutionRequestEvent
    ) -> SQLResultEvent:
        """Retrieve SQL results using the OSO DB client."""
        if not self.oso_client:
            raise ValueError("OSO DB client is not initialized.")

        try:
            return await self.execute_query(
                query.output_sql, query.id, query.synthesize_response
            )
        except Exception as e:
            logger.error(f"Error retrieving SQL results: {e}")

            return SQLResultEvent(
                id=query.id,
                input_text=query.input_text,
                output_sql=query.output_sql,
                results=[],
                error=e,
                synthesize_response=query.synthesize_response,
            )

    async def execute_query(
        self, query: str, id: str = "query_execution", synthesize_response: bool = True
    ) -> SQLResultEvent:
        """Execute a SQL query using the PyOSO client."""
        if not self.oso_client:
            raise ValueError("PyOSO client is not initialized.")

        # Example of executing a query and returning results
        results = await self.oso_client.query_oso(query)

        return SQLResultEvent(
            id=id,
            input_text=query,
            output_sql=query,
            results=results,
            synthesize_response=synthesize_response,
        )


class SQLRowsResponseSynthesisMixin(MixableWorkflow):
    """Mixin class to enable SQL response synthesis in agent workflows."""

    response_synthesis_prompt: ResourceDependency[PromptTemplate] = ResourceDependency(
        default_factory=lambda: DEFAULT_RESPONSE_SYNTHESIS_PROMPT
    )
    llm: ResourceDependency[FunctionCallingLLM]

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
