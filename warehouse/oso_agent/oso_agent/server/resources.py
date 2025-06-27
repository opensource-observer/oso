from ..resources import DefaultResourceResolver, ResourceResolver
from ..util.config import AgentConfig


async def default_resolver_factory(config: AgentConfig) -> ResourceResolver:
    """Default resolver factory that creates a resolver based on the AgentConfig."""
    from oso_agent.tool.embedding import create_embedding
    from oso_agent.tool.llm import create_llm
    from oso_agent.tool.oso_mcp_client import OsoMcpClient
    from oso_agent.tool.query_engine_tool import create_default_query_engine_tool
    from oso_agent.tool.storage_context import setup_storage_context
    from oso_semantic.testing import setup_registry

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
    registry = setup_registry()

    return DefaultResourceResolver.from_resources(
        query_engine_tool=query_engine_tool,
        llm=llm,
        embedding=embedding,
        storage_context=storage_context,
        oso_mcp_client=oso_mcp_client,
        registry=registry,
    )