"""
The default agent registry for the oso agent.
"""
import logging

from ..util.config import AgentConfig
from .agent_registry import AgentRegistry
from .react_agent import create_react_agent
from .semantic_agent import create_semantic_agent
from .sql_agent import create_sql_agent

logger = logging.getLogger(__name__)

def setup_default_agent_registry(config: AgentConfig) -> AgentRegistry:
    logger.info("Setting up the default agent registry...")
    registry = AgentRegistry(config)

    registry.add_agent("react", create_react_agent)
    registry.add_agent("sql", create_sql_agent)
    registry.add_agent("semantic", create_semantic_agent)

    logger.info("Default agent registry setup complete.")
    return registry