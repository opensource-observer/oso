"""
A workflow for translating natural language to SQL using a semantic layer.
"""

import hashlib
import logging
import typing as t

from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.tools import FunctionTool
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.core.workflow import StopEvent, step
from oso_agent.resources import ResourceDependency
from oso_agent.types import ErrorResponse
from oso_agent.types.response import StrResponse
from oso_agent.workflows.base import ResourceResolver
from oso_agent.workflows.text2sql.mixins import (
    GenericText2SQLRouter,
    OsoDBWorkflow,
    OsoVectorDatabaseMixin,
    SQLRowsResponseSynthesisMixin,
)
from oso_agent.workflows.types import (
    RetrySemanticQueryEvent,
    RowContextEvent,
    SemanticQueryEvent,
    SQLResultSummaryResponseEvent,
    StartQueryEngineEvent,
    Text2SQLGenerationEvent,
)
from oso_semantic import Registry
from oso_semantic.definition import SemanticQuery

from ..base import StartingWorkflow
from .events import Text2SQLStartEvent

logger = logging.getLogger(__name__)


class SemanticText2SQLWorkflow(
    StartingWorkflow[Text2SQLStartEvent],
    GenericText2SQLRouter,
    OsoDBWorkflow,
    SQLRowsResponseSynthesisMixin,
    OsoVectorDatabaseMixin,
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
    enable_retries: bool = True
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

    async def _get_vector_context_for_entities(self, query: str) -> str:
        """Retrieve relevant entity context from vector database to help semantic parsing."""
        try:
            vector_index = await self._get_vector_index()

            context_parts = []

            table_names = ["projects_v1", "collections_v1", "metrics_v0"]
            filtered_tables = [
                name for name in table_names if name in self.tables_to_index
            ]

            for table_name in filtered_tables:
                retriever = vector_index.as_retriever(
                    similarity_top_k=3,
                    filters=MetadataFilters(
                        filters=[ExactMatchFilter(key="table_name", value=table_name)]
                    ),
                )

                nodes = await retriever.aretrieve(query)
                if not nodes:
                    continue

                table_context = f"\n{table_name.upper()} entities:\n"
                for node in nodes:
                    table_context += f"- {node.text}\n"
                context_parts.append(table_context)

            return "\n".join(context_parts) if context_parts else ""

        except Exception as e:
            logger.warning(f"Could not retrieve vector context for entities: {e}")
            return ""

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
    async def initiate_query_engine(
        self, event: Text2SQLStartEvent
    ) -> StartQueryEngineEvent:
        """Convert Text2SQLStartEvent to StartQueryEngineEvent to trigger vector database flow."""
        if not event.id:
            event_id = hashlib.sha1(event.input.encode()).hexdigest()
            logger.debug("No ID provided for event, generated ID: %s", event_id)
        else:
            event_id = event.id

        logger.info(
            "Initiating query engine for semantic text2sql query[%s]: %s",
            event_id,
            event.input,
        )

        return StartQueryEngineEvent(
            id=event_id,
            input_text=event.input,
            synthesize_response=event.synthesize_response,
            execute_sql=event.execute_sql,
        )

    @step
    async def handle_row_context_for_semantic_translation(
        self, event: RowContextEvent
    ) -> SemanticQueryEvent | RetrySemanticQueryEvent | StopEvent:
        """Handle RowContextEvent and use vector context to enhance semantic translation."""
        logger.debug(f"Processing RowContextEvent for semantic translation: {event.id}")

        entity_context_parts = []
        for table_name, retriever in event.row_retrievers.items():
            try:
                nodes = await retriever.aretrieve(event.input_text)
                if nodes:
                    table_context = f"\n{table_name.upper()} entities:\n"
                    for node in nodes:
                        table_context += f"- {node.text}\n"
                    entity_context_parts.append(table_context)
            except Exception as e:
                logger.warning(f"Could not retrieve context from {table_name}: {e}")

        entity_context = "\n".join(entity_context_parts) if entity_context_parts else ""

        return await self._perform_semantic_translation(
            event.input_text,
            entity_context,
            event.synthesize_response,
            event.execute_sql,
            remaining_tries=self.max_retries + 1,
            error_context=[],
        )

    @step
    async def start_translation(
        self, event: RetrySemanticQueryEvent
    ) -> SemanticQueryEvent | RetrySemanticQueryEvent | StopEvent:
        """
        Translate natural language to a structured SemanticQuery.
        This step can be called at the start of a workflow or as a retry attempt.
        """
        retry_number = self.max_retries - event.remaining_tries + 1
        logger.debug(
            f"Retrying translation... attempt {retry_number}/{self.max_retries}, {event.remaining_tries} tries left"
        )
        if event.remaining_tries <= 0:
            logger.error("Exceeded max retries for semantic query translation")
            return StopEvent(
                result=ErrorResponse(
                    message="Exceeded max retries for semantic query translation"
                )
            )

        natural_language_query = event.input_text
        error_feedback = str(event.error)
        if event.error_context:
            error_feedback = f"Previous errors encountered: {'; '.join(event.error_context)}. Current error: {error_feedback}"

        entity_context = await self._get_vector_context_for_entities(
            natural_language_query
        )

        return await self._perform_semantic_translation(
            natural_language_query,
            entity_context,
            event.synthesize_response,
            event.execute_sql,
            remaining_tries=event.remaining_tries,
            error_context=event.error_context,
            error_feedback=error_feedback,
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
            synthesize_response = event.synthesize_response
            execute_sql = event.execute_sql

            event_input_id = getattr(event, "id", "")
            if not event_input_id:
                event_input_id = hashlib.sha1(event.input_text.encode()).hexdigest()
                logger.debug(
                    "No ID provided for event, generated ID: %s", event_input_id
                )

            return Text2SQLGenerationEvent(
                id=event_input_id,
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
                synthesize_response=event.synthesize_response,
                execute_sql=event.execute_sql,
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

    async def _perform_semantic_translation(
        self,
        natural_language_query: str,
        entity_context: str,
        synthesize_response: bool,
        execute_sql: bool,
        remaining_tries: int,
        error_context: list[str],
        error_feedback: str | None = None,
    ) -> SemanticQueryEvent | RetrySemanticQueryEvent:
        """Core semantic translation logic with entity context."""
        tool = self._get_semantic_tool()

        if entity_context:
            logger.debug(
                f"Using entity context for query: {natural_language_query[:50]}..."
            )

        try:
            tool_output = await tool.acall(
                natural_language_query=natural_language_query,
                error_feedback=error_feedback,
                entity_context=entity_context,
            )
            raw_output = tool_output.raw_output
            assert isinstance(raw_output, ToolResponse)
            structured_query = self._parse_semantic_tool_output(raw_output)

            logger.debug(
                f"Successfully translated to structured query: {structured_query}"
            )

            return SemanticQueryEvent(
                structured_query=structured_query,
                input_text=natural_language_query,
                remaining_tries=remaining_tries,
                error_context=error_context,
                synthesize_response=synthesize_response,
                execute_sql=execute_sql,
            )
        except Exception as e:
            logger.debug(f"Error translating natural language to structured query: {e}")

            new_error_context = error_context + [f"Translation error: {str(e)}"]

            return RetrySemanticQueryEvent(
                input_text=natural_language_query,
                error=e,
                remaining_tries=remaining_tries - 1,
                error_context=new_error_context,
                synthesize_response=synthesize_response,
                execute_sql=execute_sql,
            )
