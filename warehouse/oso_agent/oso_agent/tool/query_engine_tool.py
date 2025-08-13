from llama_index.core import StorageContext
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.tools import QueryEngineTool
from oso_agent.clients import OsoClient
from oso_agent.tool.storage_context import setup_storage_context

from ..util.config import AgentConfig
from .embedding import create_embedding
from .llm import create_llm
from .oso_text2sql import create_oso_query_engine


async def create_default_query_engine_tool(
    config: AgentConfig,
    oso_client: OsoClient,
    llm: FunctionCallingLLM | None = None,
    storage_context: StorageContext | None = None,
    embedding: BaseEmbedding | None = None,
    synthesize_response: bool = True,
):
    llm = llm or create_llm(config)

    embedding = embedding or create_embedding(config)

    storage_context = storage_context or setup_storage_context(
        config, embed_model=embedding
    )

    query_engine = await create_oso_query_engine(
        config,
        oso_client,
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
