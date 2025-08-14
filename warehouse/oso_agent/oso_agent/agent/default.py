"""
The default agent registry for the oso agent.
"""
import logging

from ..util.config import AgentConfig
from .agent_registry import AgentRegistry
from .function_text2sql import create_function_text2sql_agent_factory

logger = logging.getLogger(__name__)

async def setup_default_agent_registry(config: AgentConfig) -> AgentRegistry:
    logger.info("Setting up the default agent registry...")
    registry = AgentRegistry(config)

    registry.add_agent("function_text2sql", create_function_text2sql_agent_factory())
    registry.add_agent(
        "function_text2sql_no_synthesis",
        create_function_text2sql_agent_factory(synthesize_response=False),
    )

    if config.eagerly_load_all_agents:
        logger.info("Eagerly loading all agents in the registry...")
        await registry.eager_load_all_agents()

    logger.info("Default agent registry setup complete.")
    return registry
