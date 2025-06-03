import typing as t

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPConfig(BaseSettings):
    """Configuration for the agent and its components."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        extra="ignore",
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

    oso_api_key: str = Field(
        default="MISSING OSO API KEY",
        description="API key for OSO",
    )

   