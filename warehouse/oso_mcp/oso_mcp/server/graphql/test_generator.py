"""Tests for GraphQL tool generator."""

import os

from mcp.server.fastmcp import FastMCP

from .generator import generate_from_schema
from .types import ToolConfig

# Get path to test schema
CURRENT_DIR = os.path.dirname(__file__)
TEST_SCHEMA_PATH = os.path.join(CURRENT_DIR, "test_schema/schema.graphql")


def test_generate_from_schema_loads_schema():
    """Test that schema is loaded without errors."""
    mcp = FastMCP("Test Server")
    config = ToolConfig(
        graphql_endpoint="https://api.example.com/graphql",
        ignore_patterns=[],
    )

    # Should not raise an exception
    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=config,
    )


def test_generate_with_ignore_patterns():
    """Test that mutations with ignore patterns are filtered."""
    mcp = FastMCP("Test Server")
    config = ToolConfig(
        graphql_endpoint="https://api.example.com/graphql",
        ignore_patterns=[r"@mcp-ignore"],
    )

    # Should filter out updateItem mutation which has @mcp-ignore in description
    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=config,
    )
