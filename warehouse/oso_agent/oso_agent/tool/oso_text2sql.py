import logging
import os
from pathlib import Path
from typing import List

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.retrievers import NLSQLRetriever
from llama_index.core.schema import TextNode
from pyoso import Client

from ..util.config import AgentConfig
from .oso_sql_db import OsoSqlDatabase

logger = logging.getLogger(__name__)

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

DEFAULT_TABLES_TO_INDEX: dict[str, list[str]] = {
    "projects_v1": [
        "project_source",
        "project_namespace",
        "project_name",
        "display_name",
        "description",
    ],
    "collections_v1": [
        "collection_source",
        "collection_namespace",
        "collection_name",
        "display_name",
        "description",
    ],
    "projects_by_collection_v1": [
        "collection_source",
        "collection_namespace",
        "collection_name",
        "project_source",
        "project_namespace",
        "project_name",
    ],
    # "artifacts_by_project_v1": [
    #     "artifact_source",
    #     "artifact_namespace",
    #     "artifact_name",
    #     "project_source",
    #     "project_namespace",
    #     "project_name",
    # ],
    "metrics_v0": [
        "metric_source",
        "metric_namespace",
        "metric_name",
        "display_name",
        "description",
    ],
}


def index_oso_tables(
    *,
    sql_database: OsoSqlDatabase,
    oso_client: Client,
    table_index_dir: str,
    tables_to_index: dict[str, list[str]],
    embed_model: BaseEmbedding,
) -> dict[str, VectorStoreIndex]:
    """Index the given tables"""

    logger.info("Indexing OSO tables...")

    if not Path(table_index_dir).exists():
        os.makedirs(table_index_dir)
    vector_index_dict = {}

    for table_name in sql_database.get_usable_table_names():
        if table_name not in tables_to_index:
            vector_index_dict[table_name] = VectorStoreIndex([], embed_model=embed_model)
            continue
        columns_to_extract = tables_to_index[table_name]
        if len(columns_to_extract) == 0:
            vector_index_dict[table_name] = VectorStoreIndex([], embed_model=embed_model)
            continue

        print(f"Indexing rows in table: {table_name}")
        row_tups = []
        if not os.path.exists(f"{table_index_dir}/{table_name}"):
            # get all rows from table
            df = oso_client.to_pandas(f'SELECT * FROM "{table_name}"')

            for index, row in df.iterrows():
                column_values = []
                for col_name in columns_to_extract:
                    column_values.append(row[col_name])
                row_tups.append(tuple(column_values))

            # index each row, put into vector store index
            nodes = [TextNode(text=str(t)) for t in row_tups]

            # put into vector store index (use OpenAIEmbeddings by default)
            logger.info(f"Using embedding model: {embed_model.model_name}")
            index = VectorStoreIndex(nodes, embed_model=embed_model)

            # save index
            index.set_index_id("vector_index")
            index.storage_context.persist(f"{table_index_dir}/{table_name}")
        else:
            # rebuild storage context
            storage_context = StorageContext.from_defaults(
                persist_dir=f"{table_index_dir}/{table_name}"
            )
            # load index
            index = load_index_from_storage(storage_context, index_id="vector_index", embed_model=embed_model)
        vector_index_dict[table_name] = index

    return vector_index_dict


async def create_oso_query_engine(
    config: AgentConfig,
    oso_client: Client,
    llm: FunctionCallingLLM,
    embedding: BaseEmbedding,
    synthesize_response: bool = True,
    include_tables: List[str] | None = None,
    tables_to_index: dict[str, list[str]] | None = None,
):
    include_tables = include_tables or DEFAULT_INCLUDE_TABLES
    tables_to_index = tables_to_index or DEFAULT_TABLES_TO_INDEX

    oso_db = await OsoSqlDatabase.create(
        oso_mcp_url=config.oso_mcp_url,
        include_tables=include_tables,
    )

    logger.info(f"Using embedding model: {embedding.model_name}")
    logger.info(f"{type(embedding)}")

    table_vectors = index_oso_tables(
        sql_database=oso_db,
        oso_client=oso_client,
        table_index_dir=config.vector_storage_dir,
        tables_to_index=tables_to_index,
        embed_model=embedding,
    )

    query_engine = NLSQLTableQueryEngine(
        sql_database=oso_db,
        tables=include_tables,
        llm=llm,
        embed_model=embedding,
        synthesize_response=synthesize_response,
    )

    rows_retrievers = {
        table_name: index.as_retriever(similarity_top_k=5)
        for table_name, index in table_vectors.items()
    }

    query_engine._sql_retriever = NLSQLRetriever(
        oso_db,
        llm=llm,
        rows_retrievers=rows_retrievers,
        embed_model=embedding,
        sql_only=False,
        verbose=True,
    )

    return query_engine
