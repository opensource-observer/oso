"""Integration tests for GraphQL tool generator with dependency injection."""

import os
import typing as t
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from oso_mcp.server.config import MCPConfig
from pydantic import SecretStr

from .generator import generate_from_schema
from .mutations import RegexMutationFilter
from .types import HttpClientFactory

# Get path to test schema and queries
CURRENT_DIR = os.path.dirname(__file__)
TEST_SCHEMA_PATH = os.path.join(CURRENT_DIR, "test_schema/schema.graphql")
TEST_QUERIES_PATH = os.path.join(CURRENT_DIR, "test_queries")


@pytest.fixture
def mcp_config():
    return MCPConfig(
        oso_base_url="https://api.example.com",
        graphql_path="/graphql",
        oso_api_key=SecretStr("test_api_key"),
    )


@pytest.fixture
def mock_http_client():
    """Create a mock httpx.AsyncClient that records requests and returns canned responses."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Store requests for verification
    mock_client.requests = []

    # Mock the post method
    async def mock_post(url, json=None, **kwargs):
        # Record the request
        mock_client.requests.append(
            {
                "url": url,
                "json": json,
                "kwargs": kwargs,
            }
        )

        # Return a mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "createItem": {
                    "success": True,
                    "message": "Item created successfully",
                    "item": {
                        "id": "test-id-123",
                        "name": "Test Item",
                        "description": "A test item",
                        "count": 42,
                        "createdAt": "2024-01-01T00:00:00Z",
                    },
                }
            }
        }
        return mock_response

    mock_client.post = mock_post

    # Mock async context manager methods
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return mock_client


@pytest.fixture
def mock_http_client_factory(mock_http_client: httpx.AsyncClient) -> HttpClientFactory:
    """Return a factory that provides the mock HTTP client."""

    @asynccontextmanager
    async def factory():
        yield mock_http_client

    return factory


@pytest.mark.asyncio
async def test_generated_tool_makes_graphql_request(
    mcp_config: MCPConfig,
    mock_http_client_factory: HttpClientFactory,
    mock_http_client: t.Any,
):
    """Test that a generated tool makes the correct GraphQL request using FastMCP Client."""
    # Create MCP server
    mcp = FastMCP("Test Server")

    # Configure tool generator with injected HTTP client factory

    # Generate tools
    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=mcp_config,
        filters=[RegexMutationFilter(patterns=["@mcp-ignore"])],  # Ignore updateItem
        http_client_factory=mock_http_client_factory,
    )

    # Create FastMCP client to call the tool
    client = Client(mcp)

    async with client:
        # Call the createItem tool
        result = await client.call_tool(
            name="createItem",
            arguments={
                "input": {
                    "name": "Test Item",
                    "description": "A test item",
                    "count": 42,
                }
            },
        )

        # Verify the GraphQL request was made
        assert len(mock_http_client.requests) == 1
        request = mock_http_client.requests[0]

        # Verify endpoint
        assert request["url"] == "https://api.example.com/graphql"

        # Verify request structure
        assert "query" in request["json"]
        assert "variables" in request["json"]

        # Verify the mutation query contains the mutation name
        assert "createItem" in request["json"]["query"]

        # Verify the mutation query requests the correct fields
        for field in ["id", "name", "description", "count", "createdAt"]:
            assert field in request["json"]["query"]

        # Verify variables contain the input
        assert request["json"]["variables"]["input"]["name"] == "Test Item"
        assert request["json"]["variables"]["input"]["description"] == "A test item"
        assert request["json"]["variables"]["input"]["count"] == 42

        # Verify the result from FastMCP Client
        # Note: result.content will contain the McpSuccessResponse
        assert len(result.content) > 0


@pytest.mark.asyncio
async def test_tool_handles_graphql_errors(
    mcp_config: MCPConfig,
    mock_http_client_factory: HttpClientFactory,
    mock_http_client: t.Any,
):
    """Test that tools properly handle GraphQL errors."""

    # Modify mock to return GraphQL errors
    async def mock_post_with_error(url, json=None, **kwargs):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "errors": [
                {"message": "Field 'name' is required"},
                {"message": "Invalid input"},
            ]
        }
        return mock_response

    mock_http_client.post = mock_post_with_error

    # Create MCP server
    mcp = FastMCP("Test Server")

    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=mcp_config,
        filters=[RegexMutationFilter(patterns=["@mcp-ignore"])],
        http_client_factory=mock_http_client_factory,
    )

    # Create client
    client = Client(mcp)

    async with client:
        # Call the tool - should return error response
        raised_error = False
        try:
            await client.call_tool(
                name="createItem",
                arguments={
                    "input": {"name": "Test Item"},
                },
            )
        except ToolError:
            raised_error = True
        assert raised_error, "Expected that ToolError was raised"


@pytest.mark.asyncio
async def test_ignore_patterns_filter_mutations(
    mcp_config: MCPConfig, mock_http_client_factory: HttpClientFactory
):
    """Test that mutations with ignore patterns are not registered."""
    # Create mock client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    # Create MCP server
    mcp = FastMCP("Test Server")

    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=mcp_config,
        filters=[RegexMutationFilter(patterns=["@mcp-ignore"])],
        http_client_factory=mock_http_client_factory,
    )

    # Create client
    client = Client(mcp)

    async with client:
        # List available tools
        tools = await client.list_tools()

        # createItem should be available
        tool_names = [tool.name for tool in tools]
        assert "createItem" in tool_names

        # updateItem should NOT be available (filtered by @mcp-ignore)
        assert "updateItem" not in tool_names


@pytest.mark.asyncio
async def test_ensure_nested_items_are_not_requests(
    mcp_config: MCPConfig,
    mock_http_client_factory: HttpClientFactory,
    mock_http_client: t.Any,
):
    """Test that nested items in the response are specifically not requested
    when doing the autogenerated mutations"""

    # Create MCP server
    mcp = FastMCP("Test Server")

    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=mcp_config,
        filters=[],
        http_client_factory=mock_http_client_factory,
    )

    # Create client
    client = Client(mcp)

    async with client:
        # Call the createItem tool
        await client.call_tool(
            name="createItem",
            arguments={
                "input": {
                    "name": "Test Item",
                    "description": "A test item",
                    "count": 42,
                }
            },
        )

        # Verify only one request was made
        assert len(mock_http_client.requests) == 1

        request_json = mock_http_client.requests[0]["json"]
        assert "query" in request_json
        mutation_query = request_json["query"]

        assert "nestedItem" not in mutation_query
        assert "nestedItems" not in mutation_query


@pytest.mark.asyncio
async def test_query_tool_generation(
    mcp_config: MCPConfig,
    mock_http_client_factory: HttpClientFactory,
    mock_http_client: t.Any,
):
    """Test that query tools are generated from client .graphql files."""

    # Update mock to return query response
    async def mock_post_query(url, json=None, **kwargs):
        mock_http_client.requests.append(
            {
                "url": url,
                "json": json,
                "kwargs": kwargs,
            }
        )

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "item": {
                    "id": "item-123",
                    "name": "Test Item",
                    "description": "A test item",
                    "count": 5,
                    "createdAt": "2024-01-01T00:00:00Z",
                    "nestedItem": {
                        "id": "nested-456",
                        "title": "Nested Item Title",
                    },
                }
            }
        }
        return mock_response

    mock_http_client.post = mock_post_query

    # Create MCP server
    mcp = FastMCP("Test Server")

    # Generate tools for both mutations and queries
    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=mcp_config,
        client_schema_path=TEST_QUERIES_PATH,
        filters=[],
        http_client_factory=mock_http_client_factory,
    )

    # Create client
    client = Client(mcp)

    async with client:
        # List available tools
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]

        # Should have both mutation and query tools
        assert "createItem" in tool_names  # Mutation
        assert "GetItem" in tool_names  # Query
        assert "ListItems" in tool_names  # Query

        # Call a query tool
        result = await client.call_tool(
            name="GetItem",
            arguments={
                "variables": {"id": "item-123"},
            },
        )

        # Verify the GraphQL request was made
        assert len(mock_http_client.requests) == 1
        request = mock_http_client.requests[0]

        assert request["url"] == "https://api.example.com/graphql"
        assert "query" in request["json"]
        assert "GetItem" in request["json"]["query"]
        assert "ItemFields" in request["json"]["query"]  # Fragment should be included

        assert request["json"]["variables"]["id"] == "item-123"

        # Verify result
        assert len(result.content) > 0
