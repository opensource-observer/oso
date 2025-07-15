"""
A workflow for translating natural language to SQL using a semantic layer.
"""

import logging
import typing as t

from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import StartEvent, StopEvent, step
from oso_agent.resources import ResourceDependency
from oso_agent.types.response import StrResponse
from oso_agent.workflows.base import ResourceResolver
from oso_agent.workflows.text2sql.mixins import (
    GenericText2SQLRouter,
    OsoDBWorkflow,
    SQLRowsResponseSynthesisMixin,
)
from oso_agent.workflows.types import (
    RetrySemanticQueryEvent,
    SemanticQueryEvent,
    SQLResultSummaryResponseEvent,
    Text2SQLGenerationEvent,
)
from oso_semantic import Registry
from oso_semantic.definition import SemanticQuery

logger = logging.getLogger(__name__)


class SemanticText2SQLWorkflow(
    GenericText2SQLRouter, OsoDBWorkflow, SQLRowsResponseSynthesisMixin
):
    """
    This workflow translates natural language to SQL in two main steps:
    1. Use the 'semantic_query_tool' to parse the user's query into a
       structured SemanticQuery object.
    2. Build the SQL query from the SemanticQuery using the
       'registry' resource, which contains the database schema and
       semantic definitions.
    3. Optionally retries the translation if it fails, allowing for error feedback
        to improve the translation process.
    """

    registry: ResourceDependency[Registry]
    semantic_query_tool: ResourceDependency[FunctionTool]
    max_retries: int = 5

    def __init__(
        self,
        resolver: ResourceResolver,
        timeout: int = 30,
        max_retries: t.Optional[int] = None,
    ):
        super().__init__(timeout=timeout, resolver=resolver)
        if max_retries is not None:
            self.max_retries = max_retries
        logger.debug(
            f"Initialized SemanticText2SQLWorkflow with max_retries={self.max_retries}"
        )

    def _get_semantic_tool(self) -> FunctionTool:
        """Get the semantic query tool from the resource resolver."""
        return self.resolver.get_resource("semantic_query_tool")

    def _parse_semantic_tool_output(self, tool_output: ToolResponse) -> SemanticQuery:
        """Parse the output of the semantic query tool."""
        if tool_output.metadata is None:
            raise ValueError("No metadata in semantic query tool output")

        structured_query_data = tool_output.metadata.get("semantic_query")
        if not structured_query_data:
            raise ValueError("No semantic_query found in metadata")

        if isinstance(structured_query_data, str):
            return SemanticQuery.model_validate_json(structured_query_data)

        return SemanticQuery.model_validate(structured_query_data)

    def _build_sql_from_query(self, structured_query: SemanticQuery) -> str:
        """Build the SQL query from the structured SemanticQuery."""
        registry: Registry = self.resolver.get_resource("registry")
        query_builder = registry.select(*structured_query.selects)

        if structured_query.filters:
            for f in structured_query.filters:
                query_builder = query_builder.where(f)

        if structured_query.limit:
            query_builder = query_builder.limit(structured_query.limit)

        sql_expression = query_builder.build()
        final_sql = sql_expression.sql(pretty=True)
        logger.debug(f"Generated SQL from semantic query: {final_sql}")
        return final_sql

    @step
    async def start_translation(
        self, event: StartEvent | RetrySemanticQueryEvent
    ) -> SemanticQueryEvent | RetrySemanticQueryEvent:
        """
        Translate natural language to a structured SemanticQuery.
        This step can be called at the start of a workflow or as a retry attempt.
        """
        if isinstance(event, RetrySemanticQueryEvent):
            retry_number = self.max_retries - event.remaining_tries + 1
            logger.debug(
                f"Retrying translation... attempt {retry_number}/{self.max_retries}, {event.remaining_tries} tries left"
            )
            if event.remaining_tries <= 0:
                raise ValueError("Exceeded max retries for semantic query translation")

            natural_language_query = event.input_text
            error_feedback = str(event.error)
            if event.error_context:
                error_feedback = f"Previous errors encountered: {'; '.join(event.error_context)}. Current error: {error_feedback}"
        else:
            logger.debug("Translating natural language to structured query...")
            natural_language_query = str(event.input)
            error_feedback = None

        tool = self._get_semantic_tool()

        try:
            tool_output = await tool.acall(
                natural_language_query=natural_language_query,
                error_feedback=error_feedback,
            )
            raw_output = tool_output.raw_output
            assert isinstance(raw_output, ToolResponse)
            structured_query = self._parse_semantic_tool_output(raw_output)

            logger.debug(
                f"Successfully translated to structured query: {structured_query}"
            )

            if isinstance(event, RetrySemanticQueryEvent):
                remaining_tries = event.remaining_tries
                error_context = event.error_context
            else:
                remaining_tries = self.max_retries
                error_context = []

            return SemanticQueryEvent(
                structured_query=structured_query,
                input_text=natural_language_query,
                remaining_tries=remaining_tries,
                error_context=error_context,
            )
        except Exception as e:
            logger.debug(f"Error translating natural language to structured query: {e}")

            if isinstance(event, RetrySemanticQueryEvent):
                retry_number = self.max_retries - event.remaining_tries + 1
                new_error_context = event.error_context + [
                    f"Retry {retry_number} translation error: {str(e)}"
                ]
                remaining_tries = event.remaining_tries - 1
            else:
                new_error_context = [f"Translation error: {str(e)}"]
                remaining_tries = self.max_retries - 1

            return RetrySemanticQueryEvent(
                input_text=natural_language_query,
                error=e,
                remaining_tries=remaining_tries,
                error_context=new_error_context,
            )

    @step
    async def build_sql_from_semantic_query(
        self, event: SemanticQueryEvent
    ) -> Text2SQLGenerationEvent | RetrySemanticQueryEvent:
        """
        Build the final SQL from the structured SemanticQuery.
        """
        logger.debug("Building SQL from structured query...")
        logger.debug(f"Structured query: {event.structured_query}")
        try:
            final_sql = self._build_sql_from_query(event.structured_query)
            synthesize_response = bool(getattr(event, "synthesize_response", True))
            execute_sql = bool(getattr(event, "execute_sql", True))

            return Text2SQLGenerationEvent(
                id="semantic_query",
                input_text=event.input_text,
                output_sql=final_sql,
                synthesize_response=synthesize_response,
                execute_sql=execute_sql,
                remaining_tries=event.remaining_tries,
                error_context=event.error_context,
            )
        except Exception as e:
            logger.debug(f"Error building SQL from structured query: {e}")
            error_context = event.error_context + [f"SQL generation error: {str(e)}"]
            return RetrySemanticQueryEvent(
                input_text=event.input_text,
                error=e,
                remaining_tries=event.remaining_tries - 1,
                error_context=error_context,
            )

    @step
    async def return_response(
        self, response: SQLResultSummaryResponseEvent
    ) -> StopEvent:
        """Return the response from the SQL query."""

        logger.debug(
            f"Returning response for query[{response.id}] with summary: {response.summary}"
        )

        return StopEvent(result=StrResponse(blob=response.summary))
