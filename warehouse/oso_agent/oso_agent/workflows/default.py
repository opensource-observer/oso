"""
Provides a default workflow registry that is configured using the AgentConfig.
"""
import logging

from oso_agent.tool.storage_context import setup_storage_context

from ..tool.embedding import create_embedding
from ..tool.llm import create_llm
from ..tool.oso_text2sql import create_oso_query_engine
from ..util.config import AgentConfig
from .registry import ResolverFactory, ResourceResolver, WorkflowRegistry
from .semantic.mixins import SemanticWorkflow
from .text2sql.basic import BasicText2SQL

logger = logging.getLogger(__name__)


async def default_resolver_factory(config: AgentConfig):
    """Default resolver factory that creates a resolver based on the AgentConfig."""
    llm = create_llm(config)
    embedding = create_embedding(config)
    storage_context = setup_storage_context(config, embed_model=embedding)
    query_engine_tool = await create_oso_query_engine(
        config,
        storage_context,
        llm,
        embedding,
        synthesize_response=False,
    )

    return ResourceResolver.from_resources(
        query_engine_tool=query_engine_tool,
        llm=llm,
        embedding=embedding,
        storage_context=storage_context,
    )

async def setup_default_workflow_registry(config: AgentConfig, resolver_factory: ResolverFactory = default_resolver_factory) -> WorkflowRegistry:
    logger.info("Setting up the default agent registry...")
    registry = WorkflowRegistry(config, resolver_factory)

    registry.add_workflow("basic_text2sql", BasicText2SQL)
    registry.add_workflow("semantic_query", SemanticWorkflow)

    logger.info("Default agent registry setup complete.")
    return registry