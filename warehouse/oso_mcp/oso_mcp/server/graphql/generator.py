"""Main GraphQL tool generator orchestrator."""

import json
import logging
import typing as t
from contextlib import asynccontextmanager

import httpx
from ariadne_codegen.schema import get_graphql_schema_from_path
from attr import dataclass
from fastmcp import FastMCP
from oso_mcp.server.config import MCPConfig

from .pydantic_generator import MutationCollectorVisitor
from .queries import QueryCollectorVisitor, QueryDocumentParser, QueryDocumentTraverser
from .schema_visitor import GraphQLSchemaTypeTraverser
from .tool_generator import ToolGenerator
from .types import (
    AsyncGraphQLClient,
    GraphQLClientFactory,
    MutationFilter,
    MutationInfo,
    QueryInfo,
)

logger = logging.getLogger(__name__)


@dataclass
class _IntermediateMutationsAndQueries:
    """Holds intermediate data for mutations and queries."""

    mutations: list[MutationInfo]
    queries: list[QueryInfo]

    def get_mutation(self, name: str) -> MutationInfo | None:
        """Get mutation by name."""
        for mutation in self.mutations:
            if mutation.name == name:
                return mutation
        return None

    def get_query(self, name: str) -> QueryInfo | None:
        """Get query by name."""
        for query in self.queries:
            if query.name == name:
                return query
        return None


class OSOAsyncGraphQLClient(AsyncGraphQLClient):
    """Asynchronous GraphQL client using httpx."""

    def __init__(
        self,
        endpoint: str,
        http_client: httpx.AsyncClient,
        api_key: str,
    ):
        self.endpoint = endpoint
        self.http_client = http_client
        self.api_key = api_key

    async def execute(
        self,
        query: str,
        operation_name: str,
        variables: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> t.Any:
        """Execute a GraphQL query asynchronously.

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            Parsed JSON response from the GraphQL server
        """
        payload: dict[str, t.Any] = {
            "query": query,
            "operationName": operation_name,
        }
        if variables:
            payload["variables"] = variables
        else:
            payload["variables"] = {}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "oso-mcp-client/0.0",
        }
        logger.debug(f"Executing GraphQL request: \n\n {json.dumps(payload, indent=2)}")

        # Make HTTP request
        response = await self.http_client.post(
            self.endpoint, json=payload, headers=headers
        )
        response.raise_for_status()
        return response.json()


def default_http_client_factory(config: MCPConfig) -> GraphQLClientFactory:
    """Create a default HTTP client for GraphQL requests."""

    @asynccontextmanager
    async def _http_client_factory() -> t.AsyncGenerator[AsyncGraphQLClient, None]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=30.0)) as client:
            yield OSOAsyncGraphQLClient(
                endpoint=config.graphql_endpoint,
                http_client=client,
                api_key=config.oso_api_key.get_secret_value(),
            )

    return _http_client_factory


def generate_from_schema(
    schema_path: str,
    mcp: FastMCP,
    filters: list[MutationFilter],
    config: MCPConfig,
    client_schema_path: str | None = None,
    graphql_client_factory: GraphQLClientFactory | None = None,
) -> None:
    """Generate and register FastMCP tools from GraphQL schema.

    Args:
        schema_path: Path to GraphQL schema directory or file
        mcp: FastMCP instance to register tools on
        config: Tool configuration
        client_schema_path: Optional path to directory containing client
                          GraphQL query files
    """
    # Generate intermediate mutations and queries
    intermediate = generate_models_intermediate_mutations_and_query_info(
        schema_path, filters, client_schema_path
    )
    mutations = intermediate.mutations
    queries = intermediate.queries

    if not graphql_client_factory:
        graphql_client_factory = default_http_client_factory(config)

    # Generate and register tools
    tool_gen = ToolGenerator(
        mcp,
        mutations,
        graphql_endpoint=config.graphql_endpoint,
        graphql_client_factory=graphql_client_factory,
        queries=queries,
    )
    tool_gen.generate_mutation_tools()
    if queries:
        tool_gen.generate_query_tools()


def generate_models_intermediate_mutations_and_query_info(
    schema_path: str,
    filters: list[MutationFilter],
    client_schema_path: str | None = None,
) -> _IntermediateMutationsAndQueries:
    # Load GraphQL schema
    schema = get_graphql_schema_from_path(schema_path)

    # Extract mutations from schema using visitor pattern
    mutation_visitor = MutationCollectorVisitor(schema, filters)
    traverser = GraphQLSchemaTypeTraverser(mutation_visitor, schema=schema)
    if schema.mutation_type:
        traverser.visit(schema.mutation_type, field_name="")
    mutations = mutation_visitor.mutations

    # Extract queries from client files if provided
    queries = []
    if client_schema_path:
        # Parse client query files (parser requires schema for type resolution)
        parser = QueryDocumentParser(schema)
        query_docs = parser.parse_directory(client_schema_path)

        queries: list[QueryInfo] = []
        # Collect queries using visitor pattern with QueryDocumentTraverser
        for doc in query_docs:
            query_visitor = QueryCollectorVisitor(schema, doc)
            traverser = QueryDocumentTraverser(query_visitor, schema)
            traverser.walk(doc)
            queries.extend(query_visitor.queries)
    return _IntermediateMutationsAndQueries(mutations=mutations, queries=queries)
