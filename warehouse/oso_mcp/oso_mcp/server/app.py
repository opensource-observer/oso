import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar, Union

import requests
from mcp.server.fastmcp import Context, FastMCP

from .config import MCPConfig

# from pyoso import Client


MCP_SSE_PORT = 8000

P = TypeVar("P")
R = TypeVar("R")


@dataclass
class McpErrorResponse(Generic[P]):
    tool_name: str
    error: str
    success: bool = False
    parameters: Optional[List[P]] = None


@dataclass
class McpSuccessResponse(Generic[P, R]):
    tool_name: str
    results: List[R]
    success: bool = True
    parameters: Optional[List[P]] = None


McpResponse = Union[McpErrorResponse[P], McpSuccessResponse[P, R]]


@dataclass
class AppContext:
    # oso_client: Optional[Client] = None
    pass



def default_lifespan(config: MCPConfig):
    @asynccontextmanager
    async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
        """Manage application lifecycle with OSO client in context"""
        # api_key = config.oso_api_key

        # client = Client(api_key.get_secret_value())
        # context = AppContext(oso_client=client)
        context = AppContext()

        try:
            yield context
        finally:
            pass

    return app_lifespan


def setup_mcp_app(config: MCPConfig):
    mcp = FastMCP(
        "OSO Data Lake Explorer",
        port=config.port,
        host=config.host,
        dependencies=["pyoso", "python-dotenv", "requests"],
        lifespan=default_lifespan(config),
    )

    @mcp.tool(
        description="Convert a natural language question into a SQL query using the OSO text2sql agent. Returns the generated SQL string.",
    )
    async def query_text2sql_agent(nl_query: str, ctx: Context) -> McpResponse:
        """
        Convert a natural language question into a SQL query using the OSO text2sql agent.

        Args:
            natural_language_query (str): The user's question in plain English.
            ctx (Context): The request context.

        Returns:
            McpSuccessResponse: Generated SQL string.
            McpErrorResponse: On error, contains error details.

        Example:
            query_text2sql_agent("Show all projects in the Ethereum collection", ctx)
        """
        if ctx:
            await ctx.info(f"Converting natural language query to SQL: {nl_query}")

        api_key = config.oso_api_key
        if not api_key:
            raise ValueError("OSO API key is not available in the context")

        url = "https://www.opensource.observer/api/v1/text2sql"
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        data = {
            "id": str(uuid.uuid4()),
            "messages": [{"role": "user", "content": nl_query}],
        }

        response = requests.post(url, json=data, headers=headers)

        return McpSuccessResponse(
            tool_name="query_text2sql_agent",
            parameters=[nl_query],
            results=[response.json()["sql"]],
        )

    return mcp
