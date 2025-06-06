from llama_index.core.tools import QueryEngineTool

from .llm import create_llm
from .embedding import create_embedding
from ..util.config import AgentConfig
from .oso_text2sql import create_oso_query_engine


async def create_default_query_engine_tool(
    config: AgentConfig,
):
    llm = create_llm(config)
    embedding = create_embedding(config)
    query_engine = await create_oso_query_engine(config, llm, embedding)
    return QueryEngineTool.from_defaults(
        query_engine,
        name="oso_query_engine",
        description="Query the OSO data lake for structured data.",
    )
