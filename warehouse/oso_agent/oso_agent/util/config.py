import typing as t

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def agent_config_dict():
    """Return the configuration dictionary for the agent."""
    return SettingsConfigDict(
        env_prefix="agent_", 
        env_nested_delimiter="__"
    )

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

    @property
    def api_key(self) -> str:
        """Return the API key for the Gemini model."""
        return self.google_api_key.get_secret_value()

class GoogleGenAILLMConfig(BaseModel):
    type: t.Literal["google_genai"] = "google_genai"

    google_api_key: SecretStr
    
    model: str = Field(default="gemini-2.0-flash")

    @property
    def api_key(self) -> str:
        """Return the API key for the Gemini model."""
        return self.google_api_key.get_secret_value()

LLMConfig = t.Union[
    LocalLLMConfig,
    GeminiLLMConfig,
    GoogleGenAILLMConfig,
]

class AgentConfig(BaseSettings):
    """Configuration for the agent and its components."""

    model_config = agent_config_dict()

    agent_name: str = Field(default="react", description="Name of the agent to use")

    llm: LLMConfig = Field(discriminator="type", default_factory=lambda: LocalLLMConfig())

    oso_mcp_url: str = Field(
        default="http://localhost:8000/sse", description="URL for the OSO MCP API"
    )
    use_mcp: bool = Field(default=True, description="Whether to use MCP tools")

    enable_telemetry: bool = Field(
        default=True, description="Whether to enable OpenTelemetry instrumentation"
    )

    arize_phoenix_base_url: str = Field(
        default="http://localhost:6006",
        description="Base URL for the Arize Phoenix API",
    )

    arize_phoenix_traces_url: str = Field(
        default="",
        description="URL for the Arize Phoenix traces API",
    )

    arize_phoenix_use_cloud: bool = Field(
        default=False,
        description="Whether to use the Arize Phoenix cloud API",
    )

    arize_phoenix_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="API key for the Arize Phoenix API"
    )

    eval_dataset_text2sql: str = Field(
        default="text2sql",
        description="Arize Phoenix dataset for text2sql evaluations",
    )

    @model_validator(mode="after")
    def validate_urls(self) -> "AgentConfig":
        """Ensure URLs are properly formatted."""
        if self.arize_phoenix_use_cloud:
            if not self.arize_phoenix_api_key.get_secret_value():
                raise ValueError("Arize Phoenix API key must be set when using cloud mode")
            self.arize_phoenix_base_url = "https://app.phoenix.arize.com"
        if not self.arize_phoenix_traces_url:
            self.arize_phoenix_traces_url = f"{self.arize_phoenix_base_url}/v1/traces"
        if not self.arize_phoenix_traces_url.endswith("/"):
            self.arize_phoenix_traces_url += "/"
        return self

    def update(self, **kwargs) -> "AgentConfig":
        """Create a new config with updates applied."""
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return self
        return AgentConfig(**{**self.model_dump(), **updates})