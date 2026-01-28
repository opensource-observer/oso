"""Generate and register FastMCP tools for mutations and queries."""

import logging
import typing as t

from fastmcp import Context, FastMCP
from pydantic import BaseModel

from .mutations import GraphQLExecutor
from .queries import QueryExecutor
from .types import GraphQLClientFactory, MutationInfo, QueryInfo

logger = logging.getLogger(__name__)


class ToolGenerator:
    """Generate and register FastMCP tools for mutations and queries."""

    def __init__(
        self,
        mcp: FastMCP,
        mutations: t.List[MutationInfo],
        graphql_endpoint: str,
        graphql_client_factory: GraphQLClientFactory,
        queries: t.Optional[t.List[QueryInfo]] = None,
    ):
        """Initialize the tool generator.

        Args:
            mcp: FastMCP instance
            mutations: List of mutations to generate tools for
            config: Tool configuration
            queries: Optional list of queries to generate tools for
        """
        self.mcp = mcp
        self.mutations = mutations
        self.queries = queries or []
        self.graphql_endpoint = graphql_endpoint
        self.graphql_client_factory = graphql_client_factory

    def generate_mutation_tools(self) -> None:
        """Register all mutation tools."""
        for mutation in self.mutations:
            self._register_mutation_tool(mutation)

    def generate_query_tools(self) -> None:
        """Register all query tools."""
        for query in self.queries:
            self._register_query_tool(query)

    def _register_mutation_tool(self, mutation: MutationInfo) -> None:
        """Register mutation tool with FastMCP.

        Args:
            mutation: Mutation information
        """
        # Create the tool function
        tool_fn = self._create_mutation_tool_function(mutation)

        # Register with FastMCP decorator
        self.mcp.tool(
            description=mutation.description or f"Execute {mutation.name} mutation"
        )(tool_fn)

    def _create_mutation_tool_function(
        self,
        mutation: MutationInfo,
    ) -> t.Callable:
        """Create async tool function that accepts Pydantic model as input.

        Args:
            mutation: Mutation information

        Returns:
            Async tool function
        """
        # Capture config in closure
        graphql_endpoint = self.graphql_endpoint
        graphql_client_factory = self.graphql_client_factory

        # Create the async function dynamically
        async def tool_function(
            input: BaseModel,
            ctx: Context,  # type: ignore
        ) -> BaseModel:
            """Dynamically generated tool function for GraphQL mutation.

            Args:
                input_data: Validated input data
                ctx: MCP context

            Returns:
                Success or error response
            """
            try:
                # Log execution
                print("Executing mutation tool:", mutation.name)
                if ctx:
                    await ctx.info(f"Executing {mutation.name} mutation")

                async with graphql_client_factory() as graphql_client:
                    # Create executor for this mutation
                    executor = GraphQLExecutor(
                        endpoint=graphql_endpoint,
                        mutation=mutation,
                        graphql_client=graphql_client,
                    )

                    # Execute mutation
                    result = await executor.execute_mutation(input)

                    # Return success response
                    return result
            except Exception as e:
                logger.error(f"Error executing mutation {mutation.name}: {e}")
                raise e

        tool_function.__annotations__["input"] = mutation.input_model
        tool_function.__annotations__["return"] = mutation.payload_model

        # Set function name for better debugging
        tool_function.__name__ = mutation.name

        return tool_function

    def _register_query_tool(self, query: QueryInfo) -> None:
        """Register query tool with FastMCP.

        Args:
            query: Query information
        """
        # Create the tool function
        tool_fn = self._create_query_tool_function(query)

        # Register with FastMCP decorator
        self.mcp.tool(description=query.description or f"Execute {query.name} query")(
            tool_fn
        )

    def _create_query_tool_function(
        self,
        query: QueryInfo,
    ) -> t.Callable:
        """Create async tool function for query.

        Args:
            query: Query information

        Returns:
            Async tool function
        """
        # Capture config in closure
        graphql_endpoint = self.graphql_endpoint
        http_client_factory = self.graphql_client_factory

        # Create the async function dynamically
        async def tool_function(
            variables: BaseModel,
            ctx: Context,  # type: ignore
        ) -> BaseModel:
            """Dynamically generated tool function for GraphQL query.

            Args:
                variables: Validated variable data
                ctx: MCP context

            Returns:
                Query response data
            """
            try:
                # Log execution
                print("Executing query tool:", query.name)
                if ctx:
                    await ctx.info(f"Executing {query.name} query")

                async with http_client_factory() as http_client:
                    # Create executor for this query
                    executor = QueryExecutor(
                        endpoint=graphql_endpoint,
                        query_info=query,
                        graphql_client=http_client,
                    )

                    # Execute query
                    result = await executor.execute_query(variables)

                    # Return result
                    return result
            except Exception as e:
                logger.error(f"Error executing query {query.name}: {e}")
                raise e

        tool_function.__annotations__["variables"] = query.input_model
        tool_function.__annotations__["return"] = query.payload_model

        # Set function name for better debugging
        tool_function.__name__ = query.name

        return tool_function
