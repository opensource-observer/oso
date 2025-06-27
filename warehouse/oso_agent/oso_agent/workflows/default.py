"""
Provides a default workflow registry that is configured using the AgentConfig.
"""
import logging

from ..resources import ResolverFactory
from ..util.config import AgentConfig
from .registry import WorkflowRegistry
from .text2sql.basic import BasicText2SQL

logger = logging.getLogger(__name__)


async def setup_default_workflow_registry(config: AgentConfig, resolver_factory: ResolverFactory) -> WorkflowRegistry:
    logger.info("Setting up the default agent registry...")
    registry = WorkflowRegistry(config, resolver_factory)

    registry.add_workflow("basic_text2sql", BasicText2SQL)

    logger.info("Default agent registry setup complete.")
    return registry