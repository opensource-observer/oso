import typing as t
from typing import List, Optional

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

from ..utils.config import agent_config_dict


class LocalLLMConfig(BaseModel):
    type: t.Literal["local"] = "local"

    ollama_model: str = Field(
        default="llama3.2:3b", description="Ollama model to use for the agent"
    )
    ollama_url: str = Field(
        default="http://localhost:11434", description="URL for the Ollama API"
    )
    ollama_timeout: float = Field(
        default=60.0, description="Timeout in seconds for Ollama API requests", gt=0
    )

class GeminiLLMConfig(BaseModel):
    type: t.Literal["google_gemini"] = "google_gemini"

    google_api_key: SecretStr

    model: str = Field(default="models/gemini-2.0-flash")

class GoogleGenAILLMConfig(BaseModel):
    type: t.Literal["google_genai"] = "google_genai"

    google_api_key: SecretStr
    
    model: str = Field(default="gemini-2.0-flash")

LLMConfig = t.Union[
    LocalLLMConfig,
    GeminiLLMConfig,
    GoogleGenAILLMConfig,
]

class AgentConfig(BaseSettings):
    """Configuration for the agent and its components."""

    model_config = agent_config_dict()

    llm: LLMConfig = Field(discriminator="type", default_factory=lambda: LocalLLMConfig())

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

    def update(self, **kwargs) -> "AgentConfig":
        """Create a new config with updates applied."""
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return self
        return AgentConfig(**{**self.model_dump(), **updates})
