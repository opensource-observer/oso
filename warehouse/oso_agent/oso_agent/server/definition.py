
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ..agent.config import AgentConfig


class AgentServerConfig(AgentConfig):
    """Configuration for the agent and its components."""

    model_config = SettingsConfigDict(env_prefix="agent_")

    port: int = Field(
        default=8000, description="Port for the server to run on"
    )

    host: str = Field(
        default="127.0.1",
        description="Host for the server to run on",
    )
