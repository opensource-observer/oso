"""Execute GraphQL mutations via HTTP."""

import typing as t

import httpx
from pydantic import BaseModel

from .types import MutationInfo


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

    def _build_mutation_query(self) -> str:
        """Build GraphQL mutation query string.

        Returns:
            GraphQL mutation query string
        """
        # Build the query with all payload fields
        fields = "\n    ".join(self.mutation.payload_fields)

        query = f"""
mutation {self.mutation.name}($input: {self.mutation.graphql_input_type_name}!) {{
  {self.mutation.name}(input: $input) {{
    {fields}
  }}
}}
""".strip()

        return query
