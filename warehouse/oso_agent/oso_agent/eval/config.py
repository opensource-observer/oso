from pydantic import Field

from ..util.config import AgentConfig, agent_config_dict


class EvalConfig(AgentConfig):
    """Configuration for evaluations."""
    model_config = agent_config_dict() 

    DATASET_NAME: str = Field(
        default="test",
        description="The experimentation dataset from Arize Phoenix",
    )

