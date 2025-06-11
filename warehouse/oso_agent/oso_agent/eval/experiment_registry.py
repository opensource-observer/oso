import logging
import typing as t
from typing import Awaitable, Callable

from phoenix.experiments.types import RanExperiment

from ..agent.agent_registry import AgentRegistry
from ..util.config import AgentConfig
from .text2sql import text2sql_experiment

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for a dictionary of agents
ExperimentDict = t.Dict[str, Callable[[AgentConfig, AgentRegistry, dict[str, t.Any ]], Awaitable[RanExperiment]]]

def get_experiments() -> ExperimentDict:
    """Create and configure the ReAct agent."""
    registry: ExperimentDict = {}
    logger.info("Creating all experiments...")
    registry["text2sql"] = text2sql_experiment
    return registry
