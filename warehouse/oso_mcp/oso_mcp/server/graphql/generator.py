"""Main GraphQL tool generator orchestrator."""

import typing as t
from contextlib import asynccontextmanager

import httpx
from ariadne_codegen.schema import get_graphql_schema_from_path
from fastmcp import FastMCP
from oso_mcp.server.config import MCPConfig

from .mutations import MutationExtractor
from .pydantic_generator import PydanticModelGenerator
from .queries import QueryDocumentParser, QueryExtractor
from .tool_generator import ToolGenerator
from .types import HttpClientFactory, MutationFilter


def default_http_client_factory(config: MCPConfig) -> HttpClientFactory:
    """Create a default HTTP client for GraphQL requests."""

    @asynccontextmanager
    async def _http_client_factory() -> t.AsyncGenerator[httpx.AsyncClient, None]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=30.0)) as client:
            yield client

    return _http_client_factory


def generate_from_schema(
    schema_path: str,
    mcp: FastMCP,
    filters: list[MutationFilter],
    config: MCPConfig,
    client_schema_path: str | None = None,
    http_client_factory: HttpClientFactory | None = None,
) -> None:
    """Generate and register FastMCP tools from GraphQL schema.

    Args:
        schema_path: Path to GraphQL schema directory or file
        mcp: FastMCP instance to register tools on
        config: Tool configuration
        client_schema_path: Optional path to directory containing client
                          GraphQL query files
    """
    # Load GraphQL schema
    schema = get_graphql_schema_from_path(schema_path)

    # Create Pydantic model generator
    model_generator = PydanticModelGenerator()

    # Extract mutations from schema
    mutation_extractor = MutationExtractor(schema)
    mutations = mutation_extractor.extract_mutations(model_generator, filters)

    # Extract queries from client files if provided
    queries = []
    if client_schema_path:
        # Parse client query files
        parser = QueryDocumentParser(client_schema_path)
        query_docs = parser.parse_all()

        # Extract queries
        query_extractor = QueryExtractor()
        queries = query_extractor.extract_queries(schema, query_docs, model_generator)

    if not http_client_factory:
        http_client_factory = default_http_client_factory(config)

    # Generate and register tools
    tool_gen = ToolGenerator(
        mcp,
        mutations,
        graphql_endpoint=config.graphql_endpoint,
        http_client_factory=http_client_factory,
        queries=queries,
    )
    tool_gen.generate_mutation_tools()
    if queries:
        tool_gen.generate_query_tools()
