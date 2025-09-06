"""
A workflow for translating natural language to SQL using a semantic layer.
"""

import hashlib
import json
import logging
import typing as t

from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.tools import FunctionTool
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.core.workflow import StopEvent, step
from oso_agent.resources import ResourceDependency
from oso_agent.types import ErrorResponse
from oso_agent.types.response import StrResponse
from oso_agent.types.streaming import ThoughtsCollector
from oso_agent.workflows.base import ResourceResolver, StartingWorkflow
from oso_agent.workflows.text2sql.events import Text2SQLStartEvent
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
    thoughts_collector: ResourceDependency[ThoughtsCollector]
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

    async def _add_thought(
        self, category: str, content: str, metadata: dict[str, t.Any] | None = None
    ) -> None:
        """Add a thought to the collector."""
        thoughts_collector = self.resolver.get_resource("thoughts_collector")
        await thoughts_collector.add_thought(category, content, metadata)

    def _get_semantic_tool(self) -> FunctionTool:
        """Get the semantic query tool from the resource resolver."""
        return self.resolver.get_resource("semantic_query_tool")

    async def _retrieve_table_context(
        self, vector_index, table_name: str, query: str
    ) -> str | None:
        """Retrieve context for a specific table."""
        retriever = vector_index.as_retriever(
            similarity_top_k=3,
            filters=MetadataFilters(
                filters=[ExactMatchFilter(key="table_name", value=table_name)]
            ),
        )

        nodes = await retriever.aretrieve(query)
        if not nodes:
            return None

        table_context = f"\n{table_name.upper()} entities:\n"
        for node in nodes:
            table_context += f"- {node.text}\n"

        await self._add_thought(
            "vector_context",
            f"Retrieved {len(nodes)} context nodes for table {table_name}",
            {"table_name": table_name, "nodes_count": len(nodes)},
        )

        return table_context

    async def _get_vector_context_for_entities(self, query: str) -> str:
        """Retrieve relevant entity context from vector database to help semantic parsing."""
        try:
            await self._add_thought(
                "vector_context",
                f"Starting vector context retrieval for query: {query[:100]}...",
                {"query_length": len(query)},
            )

            vector_index = await self._get_vector_index()
            table_names = ["projects_v1", "collections_v1", "metrics_v0"]
            filtered_tables = [
                name for name in table_names if name in self.tables_to_index
            ]

            await self._add_thought(
                "vector_context",
                f"Searching vector index for tables: {filtered_tables}",
                {"tables_searched": filtered_tables},
            )

            context_parts = []
            for table_name in filtered_tables:
                table_context = await self._retrieve_table_context(
                    vector_index, table_name, query
                )
                if table_context:
                    context_parts.append(table_context)

            result = "\n".join(context_parts) if context_parts else ""
            await self._add_thought(
                "vector_context",
                f"Vector context retrieval completed. Found context for {len(context_parts)} tables",
                {
                    "context_length": len(result),
                    "tables_with_context": len(context_parts),
                },
            )

            return result

        except Exception as e:
            logger.warning(f"Could not retrieve vector context for entities: {e}")
            await self._add_thought(
                "error_handling",
                f"Vector context retrieval failed: {str(e)}",
                {"error_type": type(e).__name__},
            )
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

        await self._add_thought(
            "query_analysis",
            f"Starting semantic text2sql workflow for query: {event.input}",
            {
                "event_id": event_id,
                "synthesize_response": event.synthesize_response,
                "execute_sql": event.execute_sql,
            },
        )

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

    async def _process_retriever_context(
        self, table_name: str, retriever, input_text: str
    ) -> str | None:
        """Process context from a single retriever."""
        try:
            nodes = await retriever.aretrieve(input_text)
            if not nodes:
                return None

            table_context = f"\n{table_name.upper()} entities:\n"
            for node in nodes:
                table_context += f"- {node.text}\n"

            await self._add_thought(
                "schema_retrieval",
                f"Retrieved {len(nodes)} context nodes from {table_name}",
                {"table_name": table_name, "nodes_count": len(nodes)},
            )

            return table_context

        except Exception as e:
            logger.warning(f"Could not retrieve context from {table_name}: {e}")
            await self._add_thought(
                "error_handling",
                f"Failed to retrieve context from {table_name}: {str(e)}",
                {"table_name": table_name, "error_type": type(e).__name__},
            )
            return None

    @step
    async def handle_row_context_for_semantic_translation(
        self, event: RowContextEvent
    ) -> SemanticQueryEvent | RetrySemanticQueryEvent | StopEvent:
        """Handle RowContextEvent and use vector context to enhance semantic translation."""
        logger.debug(f"Processing RowContextEvent for semantic translation: {event.id}")

        await self._add_thought(
            "schema_retrieval",
            f"Processing row context for semantic translation. Event ID: {event.id}",
            {"event_id": event.id, "retrievers_count": len(event.row_retrievers)},
        )

        entity_context_parts = []
        for table_name, retriever in event.row_retrievers.items():
            table_context = await self._process_retriever_context(
                table_name, retriever, event.input_text
            )
            if table_context:
                entity_context_parts.append(table_context)

        entity_context = "\n".join(entity_context_parts) if entity_context_parts else ""

        await self._add_thought(
            "schema_retrieval",
            f"Row context processing completed. Generated context from {len(entity_context_parts)} tables",
            {
                "context_length": len(entity_context),
                "tables_processed": len(entity_context_parts),
            },
        )

        return await self._perform_semantic_translation(
            event.id,
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
        if isinstance(event, RetrySemanticQueryEvent):
            retry_number = self.max_retries - event.remaining_tries + 1
            logger.debug(
                f"Retrying translation... attempt {retry_number}/{self.max_retries}, {event.remaining_tries} tries left"
            )

            await self._add_thought(
                "error_handling",
                f"Retrying semantic translation. Attempt {retry_number}/{self.max_retries}",
                {
                    "retry_number": retry_number,
                    "remaining_tries": event.remaining_tries,
                    "error_context": event.error_context,
                },
            )

            if event.remaining_tries <= 0:
                logger.error("Exceeded max retries for semantic query translation")
                await self._add_thought(
                    "error_handling",
                    f"Exceeded max retries for semantic query translation. Final error context: {event.error_context}",
                    {
                        "max_retries": self.max_retries,
                        "error_context": event.error_context,
                    },
                )
                return StopEvent(
                    result=ErrorResponse(
                        message=f"Exceeded max retries for semantic query translation with error(s): {'; '.join(event.error_context)}"
                    )
                )

        natural_language_query = event.input_text
        error_feedback = str(event.error)
        if event.error_context:
            error_feedback = f"Previous errors encountered: {'; '.join(event.error_context)}. Current error: {error_feedback}"

        await self._add_thought(
            "query_analysis",
            f"Starting semantic translation for query: {natural_language_query[:100]}...",
            {
                "query_length": len(natural_language_query),
                "has_error_feedback": bool(error_feedback),
            },
        )

        entity_context = await self._get_vector_context_for_entities(
            natural_language_query
        )

        return await self._perform_semantic_translation(
            event.id,
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

        formatted_query_json = json.dumps(event.structured_query.model_dump(), indent=2)

        await self._add_thought(
            "sql_generation",
            f"Building SQL from structured semantic query:\n\n```json\n{formatted_query_json}\n```",
            {
                "selects_count": len(event.structured_query.selects),
                "filters_count": (
                    len(event.structured_query.filters)
                    if event.structured_query.filters
                    else 0
                ),
            },
        )

        try:
            final_sql = self._build_sql_from_query(event.structured_query)
            synthesize_response = event.synthesize_response
            execute_sql = event.execute_sql

            event_input_id = event.id

            await self._add_thought(
                "sql_generation",
                f"Successfully generated SQL query: {final_sql[:200]}...",
                {
                    "sql_length": len(final_sql),
                    "event_id": event_input_id,
                    "generated_sql": final_sql,
                    "structured_query_json": event.structured_query.model_dump_json(),
                },
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

            await self._add_thought(
                "error_handling",
                f"SQL generation failed: {str(e)}. Retrying...",
                {
                    "error_type": type(e).__name__,
                    "remaining_tries": event.remaining_tries - 1,
                },
            )

            return RetrySemanticQueryEvent(
                id=event.id,
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

        await self._add_thought(
            "validation",
            f"Workflow completed successfully. Returning response for query {response.id}",
            {"query_id": response.id, "summary_length": len(response.summary)},
        )

        return StopEvent(result=StrResponse(blob=response.summary))

    async def _perform_semantic_translation(
        self,
        event_id: str,
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

        await self._add_thought(
            "semantic_parsing",
            "Performing semantic translation with entity context",
            {
                "has_entity_context": bool(entity_context),
                "entity_context_length": len(entity_context),
                "has_error_feedback": bool(error_feedback),
            },
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

            formatted_json = json.dumps(structured_query.model_dump(), indent=2)

            await self._add_thought(
                "semantic_parsing",
                f"Successfully parsed natural language to structured semantic query:\n\n```json\n{formatted_json}\n```",
                {
                    "selects": [str(s) for s in structured_query.selects],
                    "filters_count": (
                        len(structured_query.filters) if structured_query.filters else 0
                    ),
                    "structured_query_json": structured_query.model_dump_json(),
                },
            )

            return SemanticQueryEvent(
                id=event_id,
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

            await self._add_thought(
                "error_handling",
                f"Semantic translation failed: {str(e)}. Will retry if attempts remaining.",
                {
                    "error_type": type(e).__name__,
                    "remaining_tries": remaining_tries - 1,
                },
            )

            return RetrySemanticQueryEvent(
                id=event_id,
                input_text=natural_language_query,
                error=e,
                remaining_tries=remaining_tries - 1,
                error_context=new_error_context,
                synthesize_response=synthesize_response,
                execute_sql=execute_sql,
            )
