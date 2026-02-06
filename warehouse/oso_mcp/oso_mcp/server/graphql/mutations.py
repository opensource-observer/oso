"""Mutation filtering and execution for GraphQL.

Note: Mutation extraction has been moved to MutationCollectorVisitor in
pydantic_generator.py, which uses the visitor pattern for schema traversal.
"""

import logging
import re
import typing as t
from enum import Enum

from pydantic import BaseModel

from .types import AsyncGraphQLClient
from .types import MutationFilter as BaseMutationFilter
from .types import MutationInfo

logger = logging.getLogger(__name__)


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

        variables = input_data.model_dump(exclude_none=True)

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

        # Convert to Pydantic model
        return self.mutation.payload_model.model_validate(data)

    def _unwrap_union_types(self, field_type: t.Any) -> t.List[t.Any]:
        """Unwrap Optional[T] by checking for Union[T, None] to get non-None
        types.

        Args:
            field_type: Type annotation to unwrap

        Returns:
            List of non-None type arguments, or empty list if not a Union
        """
        origin = t.get_origin(field_type)
        if origin is t.Union:
            args = t.get_args(field_type)
            # Filter out NoneType from Union to get the actual types
            return [arg for arg in args if arg is not type(None)]
        return []

    def _is_discriminated_union(self, unioned_type_args: t.List[t.Any]) -> bool:
        """Check if type arguments represent a discriminated union.

        Args:
            unioned_type_args: Type arguments from a Union

        Returns:
            True if this is a discriminated union (multiple BaseModel types with typename__)
        """
        return len(unioned_type_args) > 1 and all(
            isinstance(arg, type)
            and issubclass(arg, BaseModel)
            and "typename__" in arg.model_fields
            for arg in unioned_type_args
        )

    def _extract_typename_from_literal(self, typename_field: t.Any) -> str:
        """Extract typename string from a Literal field annotation.

        Args:
            typename_field: Field info for typename__ field

        Returns:
            The typename string value from the Literal annotation
        """
        typename_annotation = typename_field.annotation
        # Handle Optional[Literal["TypeName"]]
        if t.get_origin(typename_annotation) is t.Union:
            typename_args = t.get_args(typename_annotation)
            typename_annotation = next(
                arg for arg in typename_args if arg is not type(None)
            )
        # Get the literal value: Literal["TypeName"] -> "TypeName"
        return t.get_args(typename_annotation)[0]

    def _build_union_member_fragment(
        self,
        union_member: t.Type[BaseModel],
        indent_level: int,
    ) -> t.Tuple[str, str]:
        """Build an inline fragment for a single union member type.

        Args:
            union_member: Pydantic model for the union member
            indent_level: Indentation level for formatting

        Returns:
            Tuple of (typename_value, fragment_string)
        """
        indent = "  " * indent_level

        # Get the typename value from the Literal field
        typename_field = union_member.model_fields["typename__"]
        typename_value = self._extract_typename_from_literal(typename_field)

        # Build fields for this union member (excluding typename__)
        member_fields = self._build_field_selection(union_member, indent_level + 1)

        if member_fields:
            # Remove the typename__ line from member fields
            member_field_lines = [
                line for line in member_fields.split("\n") if "typename__" not in line
            ]
            member_fields_filtered = "\n".join(member_field_lines)

            fragment = (
                f"{indent}... on {typename_value} {{\n"
                f"{member_fields_filtered}\n"
                f"{indent}}}"
            )
            return typename_value, fragment

        return typename_value, ""

    def _build_discriminated_union_selection(
        self,
        field_name: str,
        unioned_type_args: t.List[t.Type[BaseModel]],
        indent_level: int,
    ) -> str:
        """Build GraphQL selection for a discriminated union field.

        Args:
            field_name: Name of the union field
            unioned_type_args: List of union member types
            indent_level: Indentation level for formatting

        Returns:
            GraphQL selection string with inline fragments
        """
        indent = "  " * indent_level
        union_selections = []

        # Always include __typename discriminator
        union_selections.append(f"{indent}__typename")

        # Build inline fragments for each union member
        for union_member in unioned_type_args:
            typename_value, fragment = self._build_union_member_fragment(
                union_member, indent_level
            )
            if fragment:
                union_selections.append(fragment)

        union_query = "\n".join(union_selections)
        return f"{indent}{field_name} {{\n{union_query}\n{indent}}}"

    def _unwrap_list_type(self, field_type: t.Any) -> t.Any:
        """Unwrap List[T] to get the inner type T.

        Args:
            field_type: Type annotation to unwrap

        Returns:
            Inner type if field_type is List[T], otherwise field_type unchanged
        """
        origin = t.get_origin(field_type)
        if origin is list:
            args = t.get_args(field_type)
            if args:
                return args[0]
        return field_type

    def _build_scalar_or_nested_field(
        self,
        field_name: str,
        field_type: t.Any,
        indent_level: int,
    ) -> str:
        """Build GraphQL selection for scalar, enum, or nested object field.

        Args:
            field_name: Name of the field
            field_type: Type of the field
            indent_level: Indentation level for formatting

        Returns:
            GraphQL selection string for this field
        """
        indent = "  " * indent_level

        # Check if the field type is a Pydantic model (nested object)
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Recursively build nested field selection
            nested_fields = self._build_field_selection(field_type, indent_level + 1)
            if nested_fields:
                return f"{indent}{field_name} {{\n{nested_fields}\n{indent}}}"
        elif isinstance(field_type, type) and issubclass(field_type, Enum):
            # Enums are scalar values in GraphQL
            return f"{indent}{field_name}"
        else:
            # Scalar field (str, int, bool, etc.)
            return f"{indent}{field_name}"

        return ""

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
        fields = []

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation

            # Check for discriminated unions within the field type
            unwrapped_union_type_args = self._unwrap_union_types(field_type)
            if self._is_discriminated_union(unwrapped_union_type_args):
                union_selection = self._build_discriminated_union_selection(
                    field_name, unwrapped_union_type_args, indent_level
                )
                fields.append(union_selection)
                continue

            # If the unwrapped union has a single type here, that means it's
            # an Optional[T], so we can just use that type as the field type
            if unwrapped_union_type_args:
                assert len(unwrapped_union_type_args) == 1, (
                    "Expected single type in unwrapped union if it's not a discriminated union"
                )
                field_type = unwrapped_union_type_args[0]

            # Unwrap List types
            field_type = self._unwrap_list_type(field_type)

            # Handle scalar, enum, or nested fields
            field_selection = self._build_scalar_or_nested_field(
                field_name, field_type, indent_level
            )
            if field_selection:
                fields.append(field_selection)

        return "\n".join(fields)

    def _build_mutation_query(self) -> str:
        """Build GraphQL mutation query string with nested field selection.

        Returns:
            GraphQL mutation query string
        """
        # Build the query with all payload fields (including nested)
        if isinstance(self.mutation.payload_model, type) and issubclass(
            self.mutation.payload_model, BaseModel
        ):
            logger.debug(f"Model fields: {self.mutation.payload_model.model_fields}")

        # Get the inner payload model specific to this mutation (we need to get
        # it based on the name of the mutation)
        payload_model_fields = self.mutation.payload_model.model_fields.get(
            self.mutation.name
        )
        logger.debug(
            f"Payload model fields for mutation {self.mutation.name}: {self.mutation.payload_model.model_fields}"
        )
        assert payload_model_fields is not None, (
            f"Expected payload model to have a field for the mutation name {self.mutation.name}"
        )
        inner_payload_model = payload_model_fields.annotation

        if isinstance(inner_payload_model, type) and issubclass(
            inner_payload_model, BaseModel
        ):
            logger.debug(
                f"Inner payload model fields: {inner_payload_model.model_fields}"
            )
            fields = self._build_field_selection(
                self.mutation.payload_model, indent_level=2
            )
            selection = f"{{ \n{fields}\n  }}"
        else:
            logger.debug(
                "Inner payload model is not a Model and is assumed to be a scalar or enum type"
            )
            selection = ""

        # Generate the argument line for the mutation (e.g. $input: InputType!)
        # by iterating over the mutation's arguments
        model_fields = self.mutation.input_model.model_fields

        input_pairs = []
        variable_pairs = []

        for field_name, info in model_fields.items():
            assert isinstance(info.json_schema_extra, dict), (
                "Expected json_schema_extra to be a dict"
            )
            assert "graphql_type_string" in info.json_schema_extra, (
                "Expected graphql_type in json_schema_extra"
            )
            graphql_type = info.json_schema_extra["graphql_type_string"]
            input_pairs.append(f"{field_name}: ${field_name}, ")
            variable_pairs.append(f"${field_name}: {graphql_type}, ")

        input_args = "".join(input_pairs).rstrip(", ")
        variable_args = "".join(variable_pairs).rstrip(", ")

        query = f"""
mutation {self.mutation.name}({variable_args}) {{
  {self.mutation.name}({input_args}) {selection}
}}
""".strip()

        return query
