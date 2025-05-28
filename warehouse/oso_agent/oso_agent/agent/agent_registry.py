import logging
import typing as t

from oso_agent.types.response import WrappedResponse

from ..types import WrappedResponseAgent
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError, AgentMissingError

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
AgentDict = t.Dict[str, WrappedResponseAgent]

AgentFactory = t.Callable[[AgentConfig], t.Awaitable[WrappedResponseAgent]]
ResponseWrapper = t.Callable[[t.Any], WrappedResponse]

class AgentRegistry:
    """Registry of all agents."""
    def __init__(
        self,
        config: AgentConfig,
    ):
        """Initialize registry."""
        self.config = config
        self.agent_factories: dict[str, AgentFactory] = {}
        self.agents: AgentDict = {}

    def add_agent(self, name: str, factory: AgentFactory):
        """Add an agent to the registry."""
        if name in self.agent_factories:
            raise AgentConfigError(f"Agent '{name}' already exists in the registry.")
        self.agent_factories[name] = factory
        logger.info(f"Agent factory '{name}' added to the registry.")

    async def get_agent(self, name: str) -> WrappedResponseAgent:
        agent = self.agents.get(name)
        if agent is None and name not in self.agent_factories:
            raise AgentMissingError(f"Agent '{name}' not found in the registry.")
        if agent is None:
            factory = self.agent_factories[name]
            agent = await factory(self.config)
            self.agents[name] = agent
            logger.info(f"Agent '{name}' lazily created and added to the registry.")
        return self.agents[name]
    
    async def eager_load_all_agents(self):
        """Eagerly load all agents in the registry."""
        logger.info("Eagerly loading all agents in the registry...")
        for name in self.agent_factories.keys():
            await self.get_agent(name)
        logger.info("All agents have been eagerly loaded.")