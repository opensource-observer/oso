"""
Provides a default workflow registry that is configured using the AgentConfig.
"""
import logging

from oso_semantic.definition import Registry
from oso_semantic.register import register_oso_models

from ..resources import DefaultResourceResolver, ResolverFactory, ResourceResolver
from ..util.config import AgentConfig
from .registry import WorkflowRegistry
from .text2sql.basic import BasicText2SQL
from .text2sql.semantic import SemanticText2SQLWorkflow

logger = logging.getLogger(__name__)

async def default_resolver_factory(config: AgentConfig) -> ResourceResolver:
    """Default resolver factory that creates a resolver based on the AgentConfig."""
    from oso_agent.tool.embedding import create_embedding
    from oso_agent.tool.llm import create_llm
    from oso_agent.tool.oso_mcp_client import OsoMcpClient
    from oso_agent.tool.oso_semantic_query_tool import create_semantic_query_tool
    from oso_agent.tool.query_engine_tool import create_default_query_engine_tool
    from oso_agent.tool.storage_context import setup_storage_context

    oso_mcp_client = OsoMcpClient(
        config.oso_mcp_url,
    )

    llm = create_llm(config)
    embedding = create_embedding(config)
    storage_context = setup_storage_context(config, embed_model=embedding)
    query_engine_tool = await create_default_query_engine_tool(
        config,
        llm=llm,
        storage_context=storage_context,
        embedding=embedding,
        synthesize_response=False,
    )
    registry = Registry()
    register_oso_models(registry)
    semantic_query_tool = create_semantic_query_tool(llm=llm, registry_description=registry.describe())

    return DefaultResourceResolver.from_resources(
        query_engine_tool=query_engine_tool,
        semantic_query_tool=semantic_query_tool,
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
    registry.add_workflow("semantic_text2sql", SemanticText2SQLWorkflow)

    logger.info("Default agent registry setup complete.")
    return registry