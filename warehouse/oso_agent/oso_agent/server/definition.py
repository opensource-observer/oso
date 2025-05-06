
from pydantic import Field

from ..agent.config import AgentConfig
from ..utils.config import agent_config_dict


class AgentServerConfig(AgentConfig):
    """Configuration for the agent and its components."""

    model_config = agent_config_dict()

    port: int = Field(
        default=8000, description="Port for the server to run on"
    )

    host: str = Field(
        default="127.0.1",
        description="Host for the server to run on",
    )
