"""Execute GraphQL queries via HTTP."""

import logging

import httpx
from pydantic import BaseModel

from .types import QueryInfo

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Execute GraphQL queries via HTTP.

    Each executor instance is specific to a single query.
    """

    def __init__(
        self,
        endpoint: str,
        query_info: QueryInfo,
        http_client: httpx.AsyncClient,
    ):
        """Initialize the query executor.

        Args:
            endpoint: GraphQL endpoint URL
            query_info: Query information
            http_client: Async HTTP client (caller can configure authentication)
        """
        self.endpoint = endpoint
        self.query_info = query_info
        self.http_client = http_client

    async def execute_query(
        self,
        variables: BaseModel,
    ) -> BaseModel:
        """Execute query.

        Args:
            variables: Pydantic model instance with validated variable data

        Returns:
            Pydantic model instance with response data

        Raises:
            httpx.HTTPError: If HTTP request fails
            Exception: If GraphQL returns errors
        """
        logger.debug(
            f"Executing query {self.query_info.name} at {self.endpoint}"
        )

        # Convert Pydantic model to dict for variables
        variables_dict = variables.model_dump()

        # Prepare request payload
        payload = {
            "query": self.query_info.query_string,
            "variables": variables_dict,
        }

        # Make HTTP request
        logger.debug(f"Sending request payload: {payload}")
        response = await self.http_client.post(self.endpoint, json=payload)
        response.raise_for_status()

        # Parse response
        result = response.json()

        # Check for GraphQL errors
        if "errors" in result:
            error_messages = [
                err.get("message", str(err)) for err in result["errors"]
            ]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

        # Get query data
        data = result.get("data", {})

        # Convert to Pydantic model
        return self.query_info.payload_model.model_validate(data)
