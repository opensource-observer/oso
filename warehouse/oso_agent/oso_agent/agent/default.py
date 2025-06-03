"""
The default agent registry for the oso agent.
"""
import logging

from ..util.config import AgentConfig
from .agent_registry import AgentRegistry
from .function_text2sql import create_function_text2sql_agent
from .react_mcp import create_react_mcp_agent
from .react_text2sql import create_react_text2sql_agent
from .semantic_agent import create_semantic_agent

logger = logging.getLogger(__name__)

async def setup_default_agent_registry(config: AgentConfig) -> AgentRegistry:
    logger.info("Setting up the default agent registry...")
    registry = AgentRegistry(config)

    registry.add_agent("function_text2sql", create_function_text2sql_agent)
    registry.add_agent("react_mcp", create_react_mcp_agent)
    registry.add_agent("react_text2sql", create_react_text2sql_agent)
    registry.add_agent("semantic", create_semantic_agent)

    if config.eagerly_load_all_agents:
        logger.info("Eagerly loading all agents in the registry...")
        await registry.eager_load_all_agents()

    logger.info("Default agent registry setup complete.")
    return registry