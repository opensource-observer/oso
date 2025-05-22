from pydantic import Field

from ..agent.config import AgentConfig
from ..utils.config import agent_config_dict


class EvalConfig(AgentConfig):
    """Configuration for evaluations."""
    model_config = agent_config_dict() 

    DATASET_NAME: str = Field(
        default="test",
        description="The experimentation dataset from Arize Phoenix",
    )

