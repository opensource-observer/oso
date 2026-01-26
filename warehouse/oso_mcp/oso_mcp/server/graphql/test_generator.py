"""Tests for GraphQL tool generator."""

import os

from fastmcp import FastMCP
from oso_mcp.server.graphql.mutations import RegexMutationFilter

from .generator import generate_from_schema
from .types import AutogenMutationsConfig

# Get path to test schema
CURRENT_DIR = os.path.dirname(__file__)
TEST_SCHEMA_PATH = os.path.join(CURRENT_DIR, "test_schema/schema.graphql")


def test_generate_from_schema_loads_schema():
    """Test that schema is loaded without errors."""
    mcp = FastMCP("Test Server")
    config = AutogenMutationsConfig(
        graphql_endpoint="https://api.example.com/graphql",
        filters=[RegexMutationFilter(patterns=[])],  # No filters
    )

    # Should not raise an exception
    generate_from_schema(
        schema_path=TEST_SCHEMA_PATH,
        mcp=mcp,
        config=config,
    )
