"""Mutation extraction, filtering, and execution for GraphQL."""

import logging
import re
import typing as t
from enum import Enum

from graphql import GraphQLInputObjectType, GraphQLObjectType, GraphQLSchema
from pydantic import BaseModel

from .pydantic_generator import PydanticModelGenerator
from .types import AsyncGraphQLClient
from .types import MutationFilter as BaseMutationFilter
from .types import MutationInfo

logger = logging.getLogger(__name__)


class MutationExtractor:
    """Extract mutation definitions from parsed GraphQL schema."""

    def __init__(self, schema: GraphQLSchema):
        """Initialize the mutation extractor.

        Args:
            schema: GraphQL schema
        """
        self.schema = schema

    def extract_mutations(
        self,
        model_generator: PydanticModelGenerator,
        filters: list[BaseMutationFilter] | None = None,
    ) -> t.List[MutationInfo]:
        """Extract all mutations and generate their Pydantic models.

        Args:
            schema: GraphQL schema
            model_generator: Pydantic model generator
            filters: Optional list of MutationFilter to filter out mutations
        Returns:
            List of mutation information
        """
        mutations = []
        mutation_type = self._get_mutation_type()

        if not mutation_type:
            return mutations

        for field_name, field in mutation_type.fields.items():
            # Get mutation description
            description = field.description or ""

            # Get input type (should be a single argument called 'input')
            input_arg = field.args.get("input")
            if not input_arg:
                # Skip mutations without input argument
                continue

            input_type = input_arg.type
            # Unwrap NonNull if present
            if hasattr(input_type, "of_type"):
                input_type = input_type.of_type

            if not isinstance(input_type, GraphQLInputObjectType):
                # Skip if input is not an input object type
                continue

            # Generate Pydantic model for input
            input_model = model_generator.generate_input_model(input_type)

            # Get return type (payload)
            return_type = field.type
            # Unwrap NonNull if present
            if hasattr(return_type, "of_type"):
                return_type = return_type.of_type

            if not isinstance(return_type, GraphQLObjectType):
                # Skip if return type is not an object type
                continue

            # Generate Pydantic model for payload
            payload_model = model_generator.generate_payload_model(return_type)

            # Extract top-level payload fields
            payload_fields = self._extract_payload_fields(return_type)

            mutation_info = MutationInfo(
                name=field_name,
                description=description,
                input_model=input_model,
                payload_model=payload_model,
                payload_fields=payload_fields,
                graphql_input_type_name=input_type.name,
            )

            # Apply filters if any
            if filters:
                if any(f.should_ignore(mutation_info) for f in filters):
                    continue
            mutations.append(mutation_info)

        return mutations

    def _get_mutation_type(
        self,
    ) -> t.Optional[GraphQLObjectType]:
        """Get the Mutation type from schema.

        Args:
            schema: GraphQL schema

        Returns:
            Mutation type or None if not present
        """
        return self.schema.mutation_type

    def _extract_payload_fields(self, payload_type: GraphQLObjectType) -> t.List[str]:
        """Get top-level and one level deep fields from payload type.

        Args:
            payload_type: GraphQL object type for mutation payload

        Returns:
            List of field names
        """
        return list(payload_type.fields.keys())


class RegexMutationFilter(BaseMutationFilter):
    """Filter mutations based on regex patterns in their descriptions."""

    def __init__(self, patterns: t.List[str]):
        """Initialize the regex mutation filter.

        Args:
            patterns: List of regex patterns to match against mutation descriptions
        """
        self.patterns = patterns

    def should_ignore(self, mutation: MutationInfo) -> bool:
        """Check if mutation should be ignored.

        Args:
            mutation: Mutation information

        Returns:
            True if mutation should be ignored, False otherwise
        """
        if not self.patterns:
            return False

        # Check if any pattern matches the mutation description
        for pattern in self.patterns:
            if self._matches_pattern(mutation.description, pattern):
                return True

        return False

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Regex pattern matching.

        Args:
            text: Text to search in
            pattern: Regex pattern to match

        Returns:
            True if pattern matches, False otherwise
        """
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            # Invalid regex pattern, ignore it
            return False


class GraphQLExecutor:
    """Execute GraphQL mutations via HTTP.

    Each executor instance is specific to a single mutation.
    """

    def __init__(
        self,
        endpoint: str,
        mutation: MutationInfo,
        graphql_client: AsyncGraphQLClient,
    ):
        """Initialize the GraphQL executor.

        Args:
            endpoint: GraphQL endpoint URL
            mutation: Mutation information
            http_client: Async HTTP client (caller can configure authentication)
        """
        self.endpoint = endpoint
        self.mutation = mutation
        self.graphql_client = graphql_client

    async def execute_mutation(
        self,
        input_data: BaseModel,
    ) -> BaseModel:
        """Execute mutation.

        Args:
            input_data: Pydantic model instance with validated input data

        Returns:
            Pydantic model instance with response data

        Raises:
            httpx.HTTPError: If HTTP request fails
            Exception: If GraphQL returns errors
        """
        logger.debug(f"Executing mutation {self.mutation.name} at {self.endpoint}")
        # Convert Pydantic model to dict for variables
        variables = {"input": input_data.model_dump()}

        # Build GraphQL mutation query
        mutation_query = self._build_mutation_query()

        # Make HTTP request
        logger.debug(f"Sending request payload: {mutation_query}")
        result = await self.graphql_client.execute(
            operation_name=self.mutation.name,
            query=mutation_query,
            variables=variables,
        )

        # Check for GraphQL errors
        if "errors" in result:
            error_messages = [err.get("message", str(err)) for err in result["errors"]]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

        # Get mutation data
        data = result.get("data", {})
        mutation_data = data.get(self.mutation.name, {})

        # Convert to Pydantic model
        return self.mutation.payload_model.model_validate(mutation_data)

    def _build_field_selection(
        self,
        model: t.Type[BaseModel],
        indent_level: int = 0,
    ) -> str:
        """Recursively build GraphQL field selection from Pydantic model.

        This method includes all fields from the Pydantic model. Fields that
        exceed max_depth are excluded during model generation.

        Args:
            model: Pydantic model to extract fields from
            indent_level: Current indentation level for formatting

        Returns:
            GraphQL field selection string
        """
        indent = "  " * indent_level
        fields = []

        for field_name, field_info in model.model_fields.items():
            # Get the field's annotation
            field_type = field_info.annotation

            # Unwrap Optional types
            origin = t.get_origin(field_type)
            if origin is t.Union:
                args = t.get_args(field_type)
                # Filter out NoneType from Union to get the actual type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    field_type = non_none_args[0]
                    origin = t.get_origin(field_type)

            # Unwrap List types
            if origin is list:
                args = t.get_args(field_type)
                if args:
                    field_type = args[0]

            # Check if the field type is a Pydantic model (nested object)
            if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                # Recursively build nested field selection
                nested_fields = self._build_field_selection(
                    field_type, indent_level + 1
                )
                if nested_fields:
                    fields.append(
                        f"{indent}{field_name} {{\n{nested_fields}\n{indent}}}"
                    )
            elif isinstance(field_type, type) and issubclass(field_type, Enum):
                # Enums are scalar values in GraphQL
                fields.append(f"{indent}{field_name}")
            else:
                # Scalar field (str, int, bool, etc.)
                fields.append(f"{indent}{field_name}")

        return "\n".join(fields)

    def _build_mutation_query(self) -> str:
        """Build GraphQL mutation query string with nested field selection.

        Returns:
            GraphQL mutation query string
        """
        # Build the query with all payload fields (including nested)
        fields = self._build_field_selection(
            self.mutation.payload_model, indent_level=2
        )

        query = f"""
mutation {self.mutation.name}($input: {self.mutation.graphql_input_type_name}!) {{
  {self.mutation.name}(input: $input) {{
{fields}
  }}
}}
""".strip()

        return query
