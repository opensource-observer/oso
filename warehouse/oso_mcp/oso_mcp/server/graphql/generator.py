"""Main GraphQL tool generator orchestrator."""

from ariadne_codegen.schema import get_graphql_schema_from_path
from fastmcp import FastMCP

from .mutation_extractor import MutationExtractor
from .pydantic_generator import PydanticModelGenerator
from .query_extractor import QueryExtractor
from .query_parser import QueryDocumentParser
from .tool_generator import ToolGenerator
from .types import AutogenMutationsConfig


def generate_from_schema(
    schema_path: str,
    mcp: FastMCP,
    config: AutogenMutationsConfig,
    client_schema_path: str | None = None,
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
    mutation_extractor = MutationExtractor()
    mutations = mutation_extractor.extract_mutations(
        schema, model_generator, config.filters
    )

    # Extract queries from client files if provided
    queries = []
    if client_schema_path:
        # Parse client query files
        parser = QueryDocumentParser(client_schema_path)
        query_docs = parser.parse_all()

        # Extract queries
        query_extractor = QueryExtractor()
        queries = query_extractor.extract_queries(schema, query_docs, model_generator)

    # Generate and register tools
    tool_gen = ToolGenerator(mcp, mutations, config, queries)
    tool_gen.generate_mutation_tools()
    if queries:
        tool_gen.generate_query_tools()
