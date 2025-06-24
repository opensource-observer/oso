from llama_index.core.tools import QueryEngineTool
from oso_agent.tool.storage_context import setup_storage_context

from ..util.config import AgentConfig
from .embedding import create_embedding
from .llm import create_llm
from .oso_text2sql import create_oso_query_engine


async def create_default_query_engine_tool(
    config: AgentConfig,
    synthesize_response: bool = True,
):
    llm = create_llm(config)

    embedding = create_embedding(config)

    storage_context = setup_storage_context(config, embed_model=embedding)

    query_engine = await create_oso_query_engine(
        config,
        storage_context,
        llm,
        embedding,
        synthesize_response=synthesize_response,
    )
    return QueryEngineTool.from_defaults(
        query_engine,
        name="oso_query_engine",
        description="Query the OSO data lake for structured data.",
    )
