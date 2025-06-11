import json
from dataclasses import dataclass
from typing import Any, Dict, List

from llama_index.tools.mcp import BasicMCPClient
from mcp.types import TextContent

from ..util.errors import AgentRuntimeError


@dataclass
class ColumnSchema:
    name: str
    type: str
    description: str = ""

class OsoMcpClient:
    """A client for interacting with the OSO MCP server."""

    def __init__(self, oso_mcp_url: str):
        self.oso_mcp_url = oso_mcp_url
        self.client = BasicMCPClient(oso_mcp_url)

    async def _call_tool_raw(self, tool_name: str, arguments: Dict) -> str:
        """Call a tool on the MCP server and return the result as a string."""
        result = await self.client.call_tool(tool_name, arguments)
        if result.isError:
            raise AgentRuntimeError(f"Error calling MCP tool {tool_name}")
        contents = result.content
        for item in contents:
            if isinstance(item, TextContent):
                return item.text
        raise AgentRuntimeError(f"Unable to find a TextContent in {len(contents)} results from MCP tool {tool_name}")

    async def call_tool(self, tool_name: str, arguments: Dict) -> List[Dict[str, Any]]:
        result_str = await self._call_tool_raw(tool_name, arguments)
        obj = json.loads(result_str)
        if not obj.get("success", False):
            raise AgentRuntimeError(f"Error calling MCP tool {tool_name}: {obj.get('error', 'Unknown error')}")
        return obj.get("results", [])

    async def query_oso(self, query: str) -> List[Dict[str, Any]]:
        """Query the OSO MCP server with a SQL query."""

        # Remove any trailing semicolon from the query
        if query.strip().endswith(";"):
            query = query.strip()[:-1]

        results = await self.call_tool("query_oso", {"sql": query})
        return results

    async def list_tables(self) -> List[str]:
        """List all tables available in the OSO MCP server."""
        tables = await self.call_tool("list_tables", {})
        table_names = [str(item["Table"]) for item in tables]
        return table_names

    async def get_table_schema(self, table_name: str) -> List[ColumnSchema]:
        """Get the schema of a specific table from the OSO MCP server."""
        results = await self.call_tool("get_table_schema", {"table_name": table_name})
        typed_results = [ColumnSchema(name=item["Column"], type=item["Type"], description=item["Comment"]) for item in results]
        return typed_results
