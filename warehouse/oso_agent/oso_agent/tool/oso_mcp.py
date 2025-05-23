import logging
from typing import List

from llama_index.core.tools import FunctionTool
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

from ..util.config import AgentConfig
from ..util.errors import AgentConfigError

logger = logging.getLogger(__name__)

ALLOWED_MCP_TOOLS = None

async def create_oso_mcp_tools(config: AgentConfig) -> List[FunctionTool]:
    """Create and return MCP tools if enabled."""
    if not config.use_mcp:
        logger.info("MCP tools disabled, skipping")
        return []

    try:
        logger.info(f"Initializing MCP client with URL: {config.oso_mcp_url}")
        mcp_client = BasicMCPClient(config.oso_mcp_url)
        mcp_tool_spec = McpToolSpec(
            client=mcp_client,
            allowed_tools=ALLOWED_MCP_TOOLS,
        )
        tools = await mcp_tool_spec.to_tool_list_async()
        tool_names = ", ".join(
            [
                str(tool._metadata.name)
                for tool in tools
                if tool._metadata.name is not None
            ]
        )
        logger.info(f"Loaded {len(tools)} MCP tools: {tool_names}")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize MCP tools: {e}")
        if config.use_mcp:
            raise AgentConfigError(f"Failed to initialize MCP tools: {e}") from e
        return []
