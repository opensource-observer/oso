"""Generate and register FastMCP tools for mutations."""

import typing as t

import httpx
from mcp.server.fastmcp import Context, FastMCP

from ..app import McpErrorResponse, McpSuccessResponse
from .executor import GraphQLExecutor
from .types import MutationInfo, ToolConfig


class ToolGenerator:
    """Generate and register FastMCP tools for mutations."""

    def __init__(
        self,
        mcp: FastMCP,
        mutations: t.List[MutationInfo],
        config: ToolConfig,
    ):
        """Initialize the tool generator.

        Args:
            mcp: FastMCP instance
            mutations: List of mutations to generate tools for
            config: Tool configuration
        """
        self.mcp = mcp
        self.mutations = mutations
        self.config = config

    def generate_tools(self) -> None:
        """Register all mutation tools."""
        for mutation in self.mutations:
            self._register_tool(mutation)

    def _register_tool(self, mutation: MutationInfo) -> None:
        """Register tool with FastMCP.

        Args:
            mutation: Mutation information
        """
        # Create the tool function
        tool_fn = self._create_tool_function(mutation)

        # Register with FastMCP decorator
        self.mcp.tool(
            description=mutation.description or f"Execute {mutation.name} mutation"
        )(tool_fn)

    def _create_tool_function(
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
        config = self.config

        # Create the async function dynamically
        async def tool_function(
            input_data: mutation.input_model, ctx: Context  # type: ignore
        ) -> t.Union[McpSuccessResponse, McpErrorResponse]:
            """Dynamically generated tool function for GraphQL mutation.

            Args:
                input_data: Validated input data
                ctx: MCP context

            Returns:
                Success or error response
            """
            try:
                # Log execution
                if ctx:
                    await ctx.info(f"Executing {mutation.name} mutation")

                # Create HTTP client with authentication
                headers = {}
                if config.api_key:
                    headers[config.auth_header_name] = f"Bearer {config.api_key}"

                async with httpx.AsyncClient(headers=headers) as http_client:
                    # Create executor for this mutation
                    executor = GraphQLExecutor(
                        endpoint=config.graphql_endpoint,
                        mutation=mutation,
                        http_client=http_client,
                    )

                    # Execute mutation
                    result = await executor.execute_mutation(input_data)

                    # Return success response
                    return McpSuccessResponse(
                        tool_name=mutation.name,
                        parameters=[input_data.model_dump()],
                        results=[result.model_dump()],
                    )
            except Exception as e:
                # Return error response
                return McpErrorResponse(
                    tool_name=mutation.name,
                    error=str(e),
                    parameters=[input_data.model_dump()] if input_data else [],
                )

        # Set function name for better debugging
        tool_function.__name__ = mutation.name

        return tool_function
