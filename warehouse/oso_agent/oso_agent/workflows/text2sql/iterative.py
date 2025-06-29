import hashlib
import logging
from typing import Union

from llama_index.core.base.response.schema import Response as ToolResponse
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.tools import QueryEngineTool
from llama_index.core.workflow import Context, StartEvent, StopEvent, step
from oso_agent.types.response import StrResponse
from oso_agent.workflows.types import (
    QueryAttempt,
    QueryAttemptStatus,
    SemanticQueryErrorEvent,
    SemanticQueryRequestEvent,
    SemanticQueryResponseEvent,
    SQLResultSummaryResponseEvent,
    Text2SQLGenerationEvent,
)
from oso_semantic import Registry

from ...resources import ResourceDependency
from ..semantic.mixins import ErrorCorrectionMixin
from .mixins import GenericText2SQLRouter, McpDBWorkflow, SQLRowsResponseSynthesisMixin

logger = logging.getLogger(__name__)

QUERY_IMPROVEMENT_PROMPT = PromptTemplate(
    """You are an expert in semantic query building. Your task is to improve a natural language query based on error feedback from a semantic query builder.

Original Query: {original_query}

Previous Attempts and Errors:
{error_history}

Current Error: {current_error}
Error Type: {error_type}

Suggestions from the semantic layer:
{suggestions}

Available Models: {available_models}
Available Attributes: {available_attributes}

Please provide an improved natural language query that addresses the error. 
Focus on:
1. Using correct model and attribute names from the available options
2. Ensuring proper relationships between models
3. Using clear, unambiguous language
4. Following the semantic layer's suggestions

Improved Query:"""
)


class IterativeText2SQL(
    GenericText2SQLRouter,
    McpDBWorkflow,
    SQLRowsResponseSynthesisMixin,
    ErrorCorrectionMixin,
):
    """
    Iterative text2sql workflow that combines basic text2sql generation
    with semantic query error correction and LLM-based query improvement.

    Process:
    1. Try basic text2sql generation first
    2. If that fails, attempt semantic query building with error correction
    3. Use LLM to improve the query based on semantic layer feedback
    4. Repeat until successful or max iterations reached
    """

    query_engine_tool: ResourceDependency[QueryEngineTool]
    llm: ResourceDependency[FunctionCallingLLM]
    registry: ResourceDependency[Registry]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_iterations = 5

    @step
    async def handle_start(
        self, ctx: Context, event: StartEvent
    ) -> Union[Text2SQLGenerationEvent, SemanticQueryRequestEvent]:
        """
        Handle the start event - first try basic text2sql approach.
        """
        event_input_id = getattr(event, "id", "")
        if not event_input_id:
            event_input_id = hashlib.sha1(event.input.encode()).hexdigest()
            logger.debug(f"No ID provided for event, generated ID: {event_input_id}")

        logger.info(
            f"Starting iterative text2sql for query[{event_input_id}]: {event.input}"
        )

        try:
            logger.info(
                f"Attempting basic text2sql generation for query[{event_input_id}]"
            )

            tool_output = await self.query_engine_tool.acall(
                input=event.input,
                context=ctx,
            )

            raw_output = tool_output.raw_output
            assert isinstance(
                raw_output, ToolResponse
            ), "Expected a ToolResponse from the query engine tool"

            if raw_output.metadata is None:
                raise ValueError("No metadata in query engine tool output")

            output_sql = raw_output.metadata.get("sql_query")
            if not output_sql:
                raise ValueError(
                    "No SQL query found in metadata of query engine tool output"
                )

            logger.info(f"Basic text2sql succeeded for query[{event_input_id}]")

            synthesize_response = bool(getattr(event, "synthesize_response", True))
            execute_sql = bool(getattr(event, "execute_sql", True))

            return Text2SQLGenerationEvent(
                id=event_input_id,
                output_sql=output_sql,
                input_text=event.input,
                synthesize_response=synthesize_response,
                execute_sql=execute_sql,
            )

        except Exception as e:
            logger.warning(f"Basic text2sql failed for query[{event_input_id}]: {e}")
            logger.info(
                f"Falling back to semantic query approach for query[{event_input_id}]"
            )

            return SemanticQueryRequestEvent(
                id=event_input_id, query=event.input, max_iterations=self.max_iterations
            )

    @step
    async def process_semantic_query_with_llm_correction(
        self, ctx: Context, request: SemanticQueryRequestEvent
    ) -> SemanticQueryResponseEvent:
        """
        Execute semantic query processing with LLM-based query improvement.

        This implements the iterative error correction process:
        1. Try semantic query building
        2. If it fails, analyze the error and get suggestions
        3. Use LLM to improve the query based on error feedback
        4. Repeat until successful or max iterations reached
        """
        attempts = []
        context = self._build_correction_context()
        current_query = request.query
        error_history = []

        for iteration in range(1, request.max_iterations + 1):
            logger.info(f"Semantic query iteration {iteration} for query[{request.id}]")

            attempt = QueryAttempt(iteration=iteration, query=current_query)

            try:
                attempt.semantic_query = current_query
                sql = self._semantic_query_to_sql(current_query)
                attempt.generated_sql = sql
                attempt.status = QueryAttemptStatus.SUCCESS

                logger.info(
                    f"Semantic query succeeded on iteration {iteration} for query[{request.id}]"
                )
                attempts.append(attempt)
                break

            except Exception as e:
                error_type, suggestions = self.analyze_error(e, context)

                attempt.error_message = str(e)
                attempt.error_type = error_type
                attempt.suggestions = suggestions
                attempt.status = QueryAttemptStatus.ERROR

                error_history.append(f"Iteration {iteration}: {str(e)}")
                context.previous_errors.append(f"Iteration {iteration}: {str(e)}")

                logger.warning(
                    f"Semantic query error in iteration {iteration} for query[{request.id}]: {e}"
                )
                logger.info(f"Error suggestions: {suggestions}")

                attempts.append(attempt)

                ctx.send_event(
                    SemanticQueryErrorEvent(
                        id=request.id,
                        error=e,
                        error_type=error_type,
                        suggestions=suggestions,
                        iteration=iteration,
                    )
                )

                if iteration < request.max_iterations:
                    try:
                        logger.info(
                            f"Attempting LLM-based query improvement for iteration {iteration + 1}"
                        )
                        current_query = await self._improve_query_with_llm(
                            original_query=request.query,
                            error_history=error_history,
                            current_error=str(e),
                            error_type=error_type,
                            suggestions=suggestions,
                            context=context,
                        )
                        logger.info(
                            f"LLM improved query for iteration {iteration + 1}: {current_query}"
                        )
                    except Exception as llm_error:
                        logger.error(f"LLM query improvement failed: {llm_error}")

        if attempts and attempts[-1].status == QueryAttemptStatus.ERROR:
            attempts[-1].status = QueryAttemptStatus.MAX_ITERATIONS_REACHED
            logger.error(
                f"Maximum iterations ({request.max_iterations}) reached without successful query generation for query[{request.id}]"
            )

        successful_attempt = self._get_successful_query(attempts)
        final_sql = successful_attempt.generated_sql if successful_attempt else None

        return SemanticQueryResponseEvent(
            id=request.id,
            attempts=attempts,
            final_sql=final_sql,
            success=successful_attempt is not None,
        )

    async def _improve_query_with_llm(
        self,
        original_query: str,
        error_history: list[str],
        current_error: str,
        error_type: str,
        suggestions: list[str],
        context,
    ) -> str:
        """
        Use LLM to improve the query based on error feedback from semantic layer.
        """
        available_attributes = []
        for model_name in context.available_models:
            if model_name in context.available_dimensions:
                dims = context.available_dimensions[model_name]
                available_attributes.append(
                    f"{model_name} dimensions: {', '.join(dims)}"
                )
            if model_name in context.available_measures:
                measures = context.available_measures[model_name]
                available_attributes.append(
                    f"{model_name} measures: {', '.join(measures)}"
                )
            if model_name in context.available_relationships:
                rels = context.available_relationships[model_name]
                available_attributes.append(
                    f"{model_name} relationships: {', '.join(rels)}"
                )

        improved_query = await self.llm.apredict(
            QUERY_IMPROVEMENT_PROMPT,
            original_query=original_query,
            error_history="\n".join(error_history),
            current_error=current_error,
            error_type=error_type,
            suggestions="\n".join(suggestions),
            available_models=", ".join(context.available_models),
            available_attributes="\n".join(available_attributes),
        )

        improved_query = improved_query.strip()
        if improved_query.startswith('"') and improved_query.endswith('"'):
            improved_query = improved_query[1:-1]

        return improved_query

    @step
    async def handle_semantic_response(
        self, response: SemanticQueryResponseEvent
    ) -> Union[Text2SQLGenerationEvent, StopEvent]:
        """
        Handle the semantic query response.
        If successful, convert to Text2SQLGenerationEvent to continue the normal flow.
        If failed, return error response.
        """
        if response.success and response.final_sql:
            logger.info(f"Semantic query processing succeeded for query[{response.id}]")

            return Text2SQLGenerationEvent(
                id=response.id,
                output_sql=response.final_sql,
                input_text=response.attempts[0].query if response.attempts else "",
                synthesize_response=True,
                execute_sql=True,
            )
        else:
            error_messages = []
            for attempt in response.attempts:
                if attempt.error_message:
                    error_messages.append(
                        f"Iteration {attempt.iteration}: {attempt.error_message}"
                    )
                    if attempt.suggestions:
                        error_messages.extend(
                            [f"  - {suggestion}" for suggestion in attempt.suggestions]
                        )

            result_message = (
                f"Failed to generate valid SQL after {len(response.attempts)} attempts:\n"
                + "\n".join(error_messages)
            )

            logger.error(
                f"Iterative text2sql failed for query[{response.id}]: {result_message}"
            )

            return StopEvent(result=StrResponse(blob=result_message))

    @step
    async def return_response(
        self, response: SQLResultSummaryResponseEvent
    ) -> StopEvent:
        """Return the final response from the SQL query execution and synthesis."""
        logger.debug(
            f"Returning final response for query[{response.id}] with summary: {response.summary}"
        )

        return StopEvent(result=StrResponse(blob=response.summary))

    def _semantic_query_to_sql(self, semantic_query: str) -> str:
        """
        Convert semantic query to SQL using the semantic layer.

        This is inherited from ErrorCorrectionMixin but included here for clarity.
        """
        from oso_semantic.query import QueryBuilder

        query_builder = QueryBuilder(self.registry)

        attributes = [attr.strip() for attr in semantic_query.split(",")]
        select_attrs = []

        for attr in attributes:
            if attr:
                alias = attr.replace(".", "_")
                select_attrs.append(f"{attr} as {alias}")

        query_builder.select(*select_attrs)
        query_expression = query_builder.build()
        return query_expression.sql(dialect="duckdb", pretty=True)

    def _get_successful_query(
        self, attempts: list[QueryAttempt]
    ) -> QueryAttempt | None:
        """Get the first successful query attempt."""
        for attempt in attempts:
            if attempt.status == QueryAttemptStatus.SUCCESS:
                return attempt
        return None
