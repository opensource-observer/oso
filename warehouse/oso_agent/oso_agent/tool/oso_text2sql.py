import logging

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.retrievers import BaseRetriever, NLSQLRetriever
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from oso_agent.clients import OsoClient

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


async def index_oso_tables(
    *,
    config: AgentConfig,
    storage_context: StorageContext,
    oso_client: OsoClient,
    embed_model: BaseEmbedding,
    tables_to_index: dict[str, list[str]] | None = None,
    include_tables: list[str] | None = None,
) -> VectorStoreIndex:
    """Index the given tables into a vector store index. Tables are separated by
    adding the table name to the metadata of the nodes.

    This is not intended to be run every time the agent runs. It should be
    called as a preprocessing step using the cli command `index-oso-tables`.
    """

    tables_to_index = tables_to_index or DEFAULT_TABLES_TO_INDEX

    include_tables = include_tables or DEFAULT_INCLUDE_TABLES
    tables_to_index = tables_to_index or DEFAULT_TABLES_TO_INDEX

    oso_db = await OsoSqlDatabase.create(
        oso_client=oso_client,
        include_tables=include_tables,
    )

    nodes: list[TextNode] = []

    for table_name in oso_db.get_usable_table_names():
        if table_name not in tables_to_index:
            continue
        columns_to_extract = tables_to_index[table_name]
        if len(columns_to_extract) == 0:
            continue

        print(f"Indexing rows in table: {table_name}")
        row_tups = []

        # get all rows from table
        df = oso_client.client.to_pandas(f'SELECT * FROM "{table_name}"')

        for index, row in df.iterrows():
            column_values = []
            for col_name in columns_to_extract:
                column_values.append(row[col_name])
            row_tups.append(tuple(column_values))

        # index each row, put into vector store index
        table_nodes = [
            TextNode(
                text=str(row),
                metadata={
                    "table_name": table_name,
                },
            )
            for row in row_tups
        ]

        nodes.extend(table_nodes)

    # put into vector store index (use OpenAIEmbeddings by default)
    logger.info(f"Using embedding model: {embed_model.model_name}")

    if config.vector_store.type == "local":
        logger.info(f"Persisting index to local directory: {config.vector_store.dir}")
        index = VectorStoreIndex(
            nodes, embed_model=embed_model, storage_context=storage_context
        )
        index.set_index_id(config.vector_store.index_name)
        index.storage_context.persist(persist_dir=config.vector_store.dir)
        return index
    else:
        logger.info(
            f"Persisting index to vector store with ID: {config.vector_store.index_id}"
        )
        logger.info(f"Number of nodes indexed: {len(nodes)}")
        index = VectorStoreIndex(
            nodes,
            embed_model=embed_model,
            storage_context=storage_context,
            is_complete_overwrite=True,
            insert_batch_size=100000,
        )
        return index
        # vector_store.add(nodes)
        # index.storage_context.persist()


async def create_oso_query_engine(
    config: AgentConfig,
    oso_client: OsoClient,
    storage_context: StorageContext,
    llm: FunctionCallingLLM,
    embedding: BaseEmbedding,
    synthesize_response: bool = True,
    include_tables: list[str] | None = None,
    tables_to_index: dict[str, list[str]] | None = None,
):
    include_tables = include_tables or DEFAULT_INCLUDE_TABLES
    tables_to_index = tables_to_index or DEFAULT_TABLES_TO_INDEX

    if config.vector_store.type == "local":
        index = load_index_from_storage(
            storage_context,
            index_id=config.vector_store.index_name,
            embed_model=embedding,
        )
    else:
        index = VectorStoreIndex.from_vector_store(
            vector_store=storage_context.vector_store, embed_model=embedding
        )

    oso_db = await OsoSqlDatabase.create(
        oso_client=oso_client,
        include_tables=include_tables,
    )

    logger.info(f"Using embedding model: {embedding.model_name}")

    query_engine = NLSQLTableQueryEngine(
        sql_database=oso_db,
        tables=include_tables,
        llm=llm,
        embed_model=embedding,
        synthesize_response=synthesize_response,
    )

    rows_retrievers: dict[str, BaseRetriever] = {}
    for table_name in oso_db.get_usable_table_names():
        if table_name not in tables_to_index:
            rows_retrievers[table_name] = VectorStoreIndex(
                [], embed_model=embedding
            ).as_retriever(similarity_top_k=1)
            continue
        rows_retrievers[table_name] = index.as_retriever(
            similarity_top_k=5,
            filters=MetadataFilters(
                filters=[ExactMatchFilter(key="table_name", value=table_name)]
            ),
        )

    query_engine._sql_retriever = NLSQLRetriever(
        oso_db,
        llm=llm,
        rows_retrievers=rows_retrievers,
        embed_model=embedding,
        sql_only=False,
        verbose=True,
    )

    return query_engine
