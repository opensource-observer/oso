from typing import List

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.query_engine import NLSQLTableQueryEngine

from ..util.config import AgentConfig
from .oso_sql_db import OsoSqlDatabase

DEFAULT_INCLUDE_TABLES = [
    "artifacts_by_project_v1",
    "collections_v1",
    "metrics_v0",
    "projects_by_collection_v1",
    "projects_v1",
    "timeseries_metrics_by_project_v0",
    "key_metrics_by_project_v0",
    "models_v0",
]

async def create_oso_query_engine(config: AgentConfig, llm: FunctionCallingLLM, embedding: BaseEmbedding, synthesize_response: bool = True, include_tables: List[str] = DEFAULT_INCLUDE_TABLES):
    oso_db = await OsoSqlDatabase.create(
        oso_mcp_url=config.oso_mcp_url,
        include_tables=include_tables,
    )

    query_engine = NLSQLTableQueryEngine(
        sql_database=oso_db, tables=include_tables, llm=llm, embed_model=embedding,
        synthesize_response=synthesize_response,
    )

    return query_engine