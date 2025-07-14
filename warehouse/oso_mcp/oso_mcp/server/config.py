import typing as t

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def mcp_config_dict():
    """Return the configuration dictionary for the MCP server."""
    return SettingsConfigDict(
        env_prefix="mcp_", 
        env_nested_delimiter="__"
    )


class MCPConfig(BaseSettings):
    """Configuration for the MCP server."""

    model_config = mcp_config_dict()

    oso_api_key: SecretStr = Field(
        default=SecretStr(""), description="API key for the OSO API"
    )

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
