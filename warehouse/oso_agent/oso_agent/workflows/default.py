"""
Provides a default workflow registry that is configured using the AgentConfig.
"""

import logging

from ..resources import DefaultResourceResolver, ResolverFactory, ResourceResolver
from ..util.config import AgentConfig, WorkflowConfig
from .registry import WorkflowRegistry
from .text2sql.basic import BasicText2SQL
from .text2sql.semantic import SemanticText2SQLWorkflow

logger = logging.getLogger(__name__)


async def default_resolver_factory(config: AgentConfig) -> ResourceResolver:
    """Creates a resource resolver using provided resources and configuration for specific workflows."""
    from oso_agent.tool.embedding import create_embedding
    from oso_agent.tool.llm import create_llm
    from oso_agent.tool.storage_context import setup_storage_context

    llm = create_llm(config)
    embedding = create_embedding(config)
    storage_context = setup_storage_context(config, embed_model=embedding)

    return DefaultResourceResolver.from_resources(
        agent_config=config,
        llm=llm,
        embedding=embedding,
        storage_context=storage_context,
    )


async def workflow_resolver_factory(
    resources: ResourceResolver,
    config: AgentConfig,
    workflow_config: WorkflowConfig,
) -> ResourceResolver:
    """Resolver factory that creates a resolver for dependant resources for workflows."""
    from oso_agent.clients.oso_client import OsoClient
    from oso_agent.tool.oso_semantic_query_tool import create_semantic_query_tool
    from oso_agent.tool.table_selector_tool import create_table_selector_tool

    llm = resources.get_resource("llm")
    embedding = resources.get_resource("embedding")
    storage_context = resources.get_resource("storage_context")

    oso_client = OsoClient(
        workflow_config.oso_api_key.get_secret_value(),
    )

    registry_description = oso_client.client.semantic.describe()

    semantic_query_tool = create_semantic_query_tool(
        llm=llm, registry_description=registry_description
    )

    table_selector_tool = create_table_selector_tool(
        llm=llm, available_models=registry_description
    )

    return DefaultResourceResolver.from_resources(
        semantic_query_tool=semantic_query_tool,
        table_selector_tool=table_selector_tool,
        oso_client=oso_client,
        registry=oso_client.client.semantic,
        agent_config=config,
        llm=llm,
        embedding=embedding,
        storage_context=storage_context,
    )


async def setup_default_workflow_registry(
    config: AgentConfig,
    default_resolver: ResourceResolver,
    workflow_resolver_factory: ResolverFactory,
) -> WorkflowRegistry:
    logger.info("Setting up the default agent registry...")
    registry = WorkflowRegistry(config, default_resolver, workflow_resolver_factory)

    registry.add_workflow("basic_text2sql", BasicText2SQL)
    registry.add_workflow("semantic_text2sql", SemanticText2SQLWorkflow)

    logger.info("Default agent registry setup complete.")
    return registry
