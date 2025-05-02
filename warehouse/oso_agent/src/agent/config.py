from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """Configuration for the agent and its components."""

    ollama_model: str = Field(
        default="llama3.2:3b", description="Ollama model to use for the agent"
    )
    ollama_url: str = Field(
        default="http://localhost:11434", description="URL for the Ollama API"
    )
    ollama_timeout: float = Field(
        default=60.0, description="Timeout in seconds for Ollama API requests", gt=0
    )

    oso_mcp_url: str = Field(
        default="http://localhost:8000/sse", description="URL for the OSO MCP API"
    )
    use_mcp: bool = Field(default=True, description="Whether to use MCP tools")
    allowed_mcp_tools: Optional[List[str]] = Field(
        default=None,
        description="List of allowed MCP tool names, or None for all tools",
    )

    enable_telemetry: bool = Field(
        default=True, description="Whether to enable OpenTelemetry instrumentation"
    )
    arize_phoenix_traces_url: str = Field(
        default="http://localhost:6006/v1/traces",
        description="URL for the Arize Phoenix traces API",
    )

    system_prompt: str = Field(
        default="You are a helpful assistant that can query the OpenSource Observer datalake.",
        description="System prompt for the agent",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AGENT_",
        extra="ignore",
    )

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load config from environment and .env file."""
        return cls()

    def update(self, **kwargs) -> "AgentConfig":
        """Create a new config with updates applied."""
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return self
        return AgentConfig(**{**self.model_dump(), **updates})
