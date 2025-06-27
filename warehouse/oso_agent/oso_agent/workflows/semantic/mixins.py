"""Semantic workflow mixins for error correction and query processing."""

import logging

from llama_index.core.workflow import Context, StartEvent, StopEvent, step
from oso_agent.workflows.base import MixableWorkflow, ResourceDependency
from oso_agent.workflows.types import (
    CorrectionContext,
    QueryAttempt,
    QueryAttemptStatus,
    SemanticQueryErrorEvent,
    SemanticQueryRequestEvent,
    SemanticQueryResponseEvent,
)
from oso_semantic import Registry
from oso_semantic.errors import (
    AttributeNotFoundError,
    InvalidAttributeReferenceError,
    ModelHasAmbiguousJoinPathError,
    ModelHasNoJoinPathError,
    SemanticQueryValidationError,
)
from oso_semantic.query import QueryBuilder

logger = logging.getLogger(__name__)


class ErrorCorrectionMixin(MixableWorkflow):
    """Mixin class to provide error analysis and correction suggestions for semantic queries."""

    registry: ResourceDependency[Registry]

    def analyze_error(
        self, error: Exception, context: CorrectionContext
    ) -> tuple[str, list[str]]:
        """
        Analyze an error and provide correction suggestions

        Returns:
            tuple: (error_type, suggestions_list)
        """
        suggestions = []
        error_type = type(error).__name__

        if isinstance(error, InvalidAttributeReferenceError):
            error_type = "invalid_attribute_reference"
            suggestions.extend(error.suggestions)
            suggestions.extend(self._suggest_attribute_corrections(error, context))

        elif isinstance(
            error, (ModelHasNoJoinPathError)
        ) or "ModelHasNoJoinPath" in str(type(error)):
            error_type = "no_join_path"
            suggestions.extend(self._suggest_join_path_corrections(error, context))

        elif isinstance(
            error, (ModelHasAmbiguousJoinPathError)
        ) or "ModelHasAmbiguousJoinPath" in str(type(error)):
            error_type = "ambiguous_join_path"
            suggestions.extend(self._suggest_disambiguation(error, context))

        elif isinstance(error, AttributeNotFoundError):
            error_type = "attribute_not_found"
            suggestions.extend(
                self._suggest_attribute_not_found_corrections(error, context)
            )

        elif isinstance(error, SemanticQueryValidationError):
            error_type = "query_validation_error"
            suggestions.extend(error.suggestions)

        elif isinstance(error, ValueError):
            error_type = "validation_error"
            suggestions.extend(self._suggest_validation_corrections(error, context))

        else:
            error_type = "unknown_error"
            suggestions.append("Review the query syntax and available models")

        return error_type, suggestions

    def _suggest_attribute_corrections(
        self, error: InvalidAttributeReferenceError, context: CorrectionContext
    ) -> list[str]:
        """Suggest corrections for invalid attribute references"""
        suggestions = []

        if hasattr(error, "reference"):
            ref_str = str(error.reference)
            parts = ref_str.split(".")

            if len(parts) >= 2:
                model_name = parts[0]

                if model_name in context.available_dimensions:
                    dim_names = [
                        str(getattr(dim, "name", dim))
                        for dim in context.available_dimensions[model_name]
                    ]
                    suggestions.append(
                        f"Available dimensions for {model_name}: {', '.join(dim_names)}"
                    )

                if model_name in context.available_measures:
                    measure_names = [
                        str(getattr(measure, "name", measure))
                        for measure in context.available_measures[model_name]
                    ]
                    suggestions.append(
                        f"Available measures for {model_name}: {', '.join(measure_names)}"
                    )

                if model_name in context.available_relationships:
                    rel_names = [
                        str(getattr(rel, "name", rel))
                        for rel in context.available_relationships[model_name]
                    ]
                    suggestions.append(
                        f"Available relationships for {model_name}: {', '.join(rel_names)}"
                    )

        return suggestions

    def _suggest_attribute_not_found_corrections(
        self, error: AttributeNotFoundError, context: CorrectionContext
    ) -> list[str]:
        """Suggest corrections for attribute not found errors"""
        suggestions = []

        model_name = error.model_name
        attribute_name = error.attribute_name

        all_attributes = []
        if model_name in context.available_dimensions:
            all_attributes.extend(context.available_dimensions[model_name])
        if model_name in context.available_measures:
            all_attributes.extend(context.available_measures[model_name])
        if model_name in context.available_relationships:
            all_attributes.extend(context.available_relationships[model_name])

        attr_names = [str(getattr(attr, "name", attr)) for attr in all_attributes]
        similar_attrs = [
            attr_name
            for attr_name in attr_names
            if attr_name.lower().startswith(attribute_name.lower()[:3])
            or attribute_name.lower() in attr_name.lower()
        ]

        if similar_attrs:
            suggestions.append(
                f"Did you mean one of these attributes: {', '.join(similar_attrs[:5])}"
            )

        if model_name in context.available_dimensions:
            dim_names = [
                str(getattr(dim, "name", dim))
                for dim in context.available_dimensions[model_name]
            ]
            suggestions.append(
                f"Available dimensions for {model_name}: {', '.join(dim_names)}"
            )
        if model_name in context.available_measures:
            measure_names = [
                str(getattr(measure, "name", measure))
                for measure in context.available_measures[model_name]
            ]
            suggestions.append(
                f"Available measures for {model_name}: {', '.join(measure_names)}"
            )
        if model_name in context.available_relationships:
            rel_names = [
                str(getattr(rel, "name", rel))
                for rel in context.available_relationships[model_name]
            ]
            suggestions.append(
                f"Available relationships for {model_name}: {', '.join(rel_names)}"
            )

        return suggestions

    def _suggest_join_path_corrections(
        self, error: Exception, context: CorrectionContext
    ) -> list[str]:
        """Suggest corrections for missing join paths"""
        suggestions = [
            "Check if the models you're trying to join have defined relationships",
            "Consider using an intermediate model to establish the join path",
            "Verify that the models exist in the registry",
        ]
        return suggestions

    def _suggest_disambiguation(
        self, error: Exception, context: CorrectionContext
    ) -> list[str]:
        """Suggest corrections for ambiguous join paths"""
        suggestions = [
            "Use the arrow operator (->) to specify the join path explicitly",
            "For example: 'github_event.from->artifact.name' or 'github_event.to->artifact.name'",
            "Check the available relationships to understand possible paths",
        ]
        return suggestions

    def _suggest_validation_corrections(
        self, error: ValueError, context: CorrectionContext
    ) -> list[str]:
        """Suggest corrections for validation errors"""
        error_msg = str(error).lower()
        suggestions = []

        if "not found" in error_msg:
            suggestions.append("Check the spelling of model and attribute names")
            suggestions.append(
                f"Available models: {', '.join(context.available_models)}"
            )

        if "already exists" in error_msg:
            suggestions.append("Use unique names for attributes in your query")

        if "reference" in error_msg and "self" in error_msg:
            suggestions.append(
                "Use 'self' keyword when referencing the current model in expressions"
            )

        return suggestions

    def _build_correction_context(self) -> CorrectionContext:
        """Build context information for error correction"""
        context = CorrectionContext()

        context.available_models = list(self.registry.models.keys())

        for model_name, model in self.registry.models.items():
            context.available_dimensions[model_name] = [
                dim.name for dim in model.dimensions
            ]
            context.available_measures[model_name] = [
                measure.name for measure in model.measures
            ]
            context.available_relationships[model_name] = [
                rel.name for rel in model.relationships
            ]

        return context


class SemanticWorkflow(ErrorCorrectionMixin):
    """Workflow for semantic query processing with error and correction loop."""

    registry: ResourceDependency[Registry]

    @step
    async def handle_start(
        self, ctx: Context, event: StartEvent
    ) -> SemanticQueryRequestEvent:
        """Handle the start event and convert to semantic query request."""
        query_input = getattr(event, "input", "") or str(event)
        event_id = getattr(event, "id", f"semantic_{hash(query_input)}")

        return SemanticQueryRequestEvent(
            id=event_id, query=query_input, max_iterations=5
        )

    @step
    async def process_semantic_query(
        self, ctx: Context, request: SemanticQueryRequestEvent
    ) -> SemanticQueryResponseEvent:
        """
        Execute the error and correction loop workflow

        Args:
            request: The semantic query request event

        Returns:
            SemanticQueryResponseEvent with attempt history and results
        """
        attempts = []
        context = self._build_correction_context()
        current_query = request.query

        for iteration in range(1, request.max_iterations + 1):
            logger.info("Starting iteration %d", iteration)

            attempt = QueryAttempt(iteration=iteration, query=current_query)

            try:
                attempt.semantic_query = current_query
                sql = self._semantic_query_to_sql(current_query)
                attempt.generated_sql = sql
                attempt.status = QueryAttemptStatus.SUCCESS

                logger.info("Successfully generated SQL in iteration %d", iteration)
                attempts.append(attempt)
                break

            except Exception as e:  # pylint: disable=broad-except
                error_type, suggestions = self.analyze_error(e, context)

                attempt.error_message = str(e)
                attempt.error_type = error_type
                attempt.suggestions = suggestions
                attempt.status = QueryAttemptStatus.ERROR

                context.previous_errors.append(f"Iteration {iteration}: {str(e)}")

                logger.warning("Error in iteration %d: %s", iteration, e)
                logger.info("Suggestions: %s", suggestions)

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

        if attempts and attempts[-1].status == QueryAttemptStatus.ERROR:
            attempts[-1].status = QueryAttemptStatus.MAX_ITERATIONS_REACHED
            logger.error(
                "Maximum iterations (%d) reached without successful query generation",
                request.max_iterations,
            )

        successful_attempt = self._get_successful_query(attempts)
        final_sql = successful_attempt.generated_sql if successful_attempt else None

        return SemanticQueryResponseEvent(
            id=request.id,
            attempts=attempts,
            final_sql=final_sql,
            success=successful_attempt is not None,
        )

    def _semantic_query_to_sql(self, semantic_query: str) -> str:
        """
        Convert semantic query to SQL using the semantic layer

        Args:
            semantic_query: Semantic query string (e.g., "artifact.name, project.name")

        Returns:
            Generated SQL string
        """
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

    @step
    async def handle_semantic_response(
        self, response: SemanticQueryResponseEvent
    ) -> StopEvent:
        """Handle the semantic query response and return final result."""
        if response.success:
            result_message = f"Successfully generated SQL:\n{response.final_sql}"
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
                f"Failed to generate SQL after {len(response.attempts)} attempts:\n"
                + "\n".join(error_messages)
            )

        return StopEvent(result=result_message)

    def _get_successful_query(
        self, attempts: list[QueryAttempt]
    ) -> QueryAttempt | None:
        """Get the first successful query attempt"""
        for attempt in attempts:
            if attempt.status == QueryAttemptStatus.SUCCESS:
                return attempt
        return None
