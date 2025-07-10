"""
A workflow for translating natural language to SQL using a semantic layer.
"""

import logging

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
    2. Use the 'registry' and the structured query to build the final SQL.
    """

    registry: ResourceDependency[Registry]
    semantic_query_tool: ResourceDependency[FunctionTool]

    def __init__(self, resolver: ResourceResolver, timeout: int = 30):
        super().__init__(timeout=timeout, resolver=resolver)
        logger.info("Initialized SemanticText2SQLWorkflow")

    @step
    async def start_translation(self, event: StartEvent) -> SemanticQueryEvent:
        """
        Translate natural language to a structured SemanticQuery.
        """
        logger.info("Translating natural language to structured query...")
        natural_language_query = str(event.input)

        tool = self.resolver.get_resource("semantic_query_tool")

        tool_output = await tool.acall(natural_language_query)

        raw_output = tool_output.raw_output
        assert isinstance(
            raw_output, ToolResponse
        ), "Expected a ToolResponse from the semantic query tool"

        if raw_output.metadata is None:
            raise ValueError("No metadata in semantic query tool output")

        structured_query_data = raw_output.metadata.get("semantic_query")
        if not structured_query_data:
            raise ValueError("No semantic_query found in metadata")

        if isinstance(structured_query_data, str):
            structured_query = SemanticQuery.model_validate_json(structured_query_data)
        else:
            structured_query = SemanticQuery.model_validate(structured_query_data)

        logger.info(f"Successfully translated to structured query: {structured_query}")
        return SemanticQueryEvent(
            structured_query=structured_query, input_text=natural_language_query
        )

    @step
    async def build_sql_from_semantic_query(
        self, event: SemanticQueryEvent
    ) -> Text2SQLGenerationEvent:
        """
        Build the final SQL from the structured SemanticQuery.
        """
        logger.info("Building SQL from structured query...")
        structured_query = event.structured_query

        registry: Registry = self.resolver.get_resource("registry")

        query_builder = registry.select(*structured_query.selects)

        if structured_query.filters:
            for f in structured_query.filters:
                query_builder = query_builder.where(f)

        if structured_query.limit:
            query_builder = query_builder.add_limit(structured_query.limit)

        sql_expression = query_builder.build()
        final_sql = sql_expression.sql(pretty=True)

        synthesize_response = bool(getattr(event, "synthesize_response", True))
        execute_sql = bool(getattr(event, "execute_sql", True))

        return Text2SQLGenerationEvent(
            id="semantic_query",
            input_text=event.input_text,
            output_sql=final_sql,
            synthesize_response=synthesize_response,
            execute_sql=execute_sql,
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
