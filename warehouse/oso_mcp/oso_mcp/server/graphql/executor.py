"""Execute GraphQL mutations via HTTP."""

import logging
import typing as t
from enum import Enum

import httpx
from pydantic import BaseModel

from .types import MutationInfo

logger = logging.getLogger(__name__)


class GraphQLExecutor:
    """Execute GraphQL mutations via HTTP.

    Each executor instance is specific to a single mutation.
    """

    def __init__(
        self,
        endpoint: str,
        mutation: MutationInfo,
        http_client: httpx.AsyncClient,
    ):
        """Initialize the GraphQL executor.

        Args:
            endpoint: GraphQL endpoint URL
            mutation: Mutation information
            http_client: Async HTTP client (caller can configure authentication)
        """
        self.endpoint = endpoint
        self.mutation = mutation
        self.http_client = http_client

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

        # Prepare request payload
        payload = {
            "query": mutation_query,
            "variables": variables,
        }

        # Make HTTP request
        logger.debug(f"Sending request payload: {payload}")
        response = await self.http_client.post(self.endpoint, json=payload)
        response.raise_for_status()

        # Parse response
        result = response.json()

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
