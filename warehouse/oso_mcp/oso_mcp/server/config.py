import typing as t

from oso_agent.util.config import AgentConfig
from pydantic import Field


class MCPConfig(AgentConfig):

    host: str = Field(
        default="127.0.0.1",
        description="Host for the mcp server to run on",
    )

    port: int = Field(
        default=8000, description="Port for the mcp server to run on"
    )

    transport: t.Literal['sse', 'stdio'] = Field(
        default="sse",
        description="The MCP transport.",
    )
