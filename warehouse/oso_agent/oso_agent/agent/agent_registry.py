import logging
import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentMissingError
from .react_agent import create_react_agent
from .sql_agent import create_sql_agent

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
AgentDict = t.Dict[str, BaseWorkflowAgent]

async def _create_agents(config: AgentConfig) -> AgentDict:
    """Create and configure the ReAct agent."""
    registry: AgentDict = {}

    try:
        logger.info("Creating all agents...")
        registry["react"] = await create_react_agent(config)
        registry["sql"] = await create_sql_agent(config)
        return registry
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise AgentConfigError(f"Failed to create agent: {e}") from e

class AgentRegistry:
    """Registry of all agents."""
    def __init__(
        self,
        config: AgentConfig,
        agents: AgentDict = {},
    ):
        """Initialize registry."""
        self.config = config
        self.agents  = agents

    @classmethod
    async def create(cls, config: AgentConfig):
        logger.info("Initializing the OSO agent registry...")
        agents = await _create_agents(config)
        registry = cls(config, agents)
        logger.info("... agent registry ready")
        return registry

    def get_agent(self, name: str) -> BaseWorkflowAgent:
        agent = self.agents.get(name)
        if agent is None:
            raise AgentMissingError(f"Agent '{name}' not found in the registry.")
        return self.agents[name]