"""Main GraphQL tool generator orchestrator."""

from ariadne_codegen.schema import get_graphql_schema_from_path
from fastmcp import FastMCP

from .mutation_extractor import MutationExtractor
from .mutation_filter import RegexMutationFilter
from .pydantic_generator import PydanticModelGenerator
from .tool_generator import ToolGenerator
from .types import ToolConfig


def generate_from_schema(
    schema_path: str,
    mcp: FastMCP,
    config: ToolConfig,
) -> None:
    """Generate and register FastMCP tools from GraphQL schema.

    Args:
        schema_path: Path to GraphQL schema directory or file
        mcp: FastMCP instance to register tools on
        config: Tool configuration
    """
    # Load GraphQL schema
    schema = get_graphql_schema_from_path(schema_path)

    # Create Pydantic model generator
    model_generator = PydanticModelGenerator()

    # Extract mutations from schema
    extractor = MutationExtractor()
    mutations = extractor.extract_mutations(schema, model_generator)

    # Filter mutations based on ignore patterns
    if config.ignore_patterns:
        filter_impl = RegexMutationFilter(config.ignore_patterns)
        mutations = [
            mutation
            for mutation in mutations
            if not filter_impl.should_ignore(mutation)
        ]

    # Generate and register tools
    tool_gen = ToolGenerator(mcp, mutations, config)
    tool_gen.generate_tools()
