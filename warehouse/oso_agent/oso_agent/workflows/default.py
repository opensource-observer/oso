"""
Provides a default workflow registry that is configured using the AgentConfig.
"""
import logging

from oso_agent.tool.oso_mcp_client import OsoMcpClient
from oso_agent.tool.query_engine_tool import create_default_query_engine_tool
from oso_agent.tool.storage_context import setup_storage_context
from oso_semantic.testing import setup_registry

from ..tool.embedding import create_embedding
from ..tool.llm import create_llm
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
    query_engine_tool = await create_default_query_engine_tool(
        config,
    )
    oso_mcp_client = OsoMcpClient(config.oso_mcp_url)

    registry = setup_registry()

    return ResourceResolver.from_resources(
        query_engine_tool=query_engine_tool,
        llm=llm,
        embedding=embedding,
        storage_context=storage_context,
        oso_mcp_client=oso_mcp_client,
        registry=registry,
    )

async def setup_default_workflow_registry(config: AgentConfig, resolver_factory: ResolverFactory = default_resolver_factory) -> WorkflowRegistry:
    logger.info("Setting up the default agent registry...")
    registry = WorkflowRegistry(config, resolver_factory)

    registry.add_workflow("basic_text2sql", BasicText2SQL)
    registry.add_workflow("semantic_text2sql", SemanticWorkflow)

    logger.info("Default agent registry setup complete.")
    return registry