import logging

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.vector_stores.vertexaivectorsearch import VertexAIVectorStore
from oso_agent.util.config import AgentConfig

logger = logging.getLogger(__name__)


def setup_storage_context(config: AgentConfig, embed_model: BaseEmbedding):
    """Setup the storage context for the agent.

    This changes based on the vector store used. This is a hack for now until we
    get a better dependency injection setup.

    """

    # Create the vector store
    if config.vector_store.type == "local":
        logger.info("Setting up local vector store")
        try:
            return StorageContext.from_defaults(persist_dir=config.vector_store.dir)
        except FileNotFoundError:
            logger.info(
                "Failed to load local vector store attempting to initialize a new one"
            )

            # Setup an empty storage context if the directory does not exist
            index = VectorStoreIndex([], embed_model=embed_model)
            index.storage_context.persist(persist_dir=config.vector_store.dir)
            return StorageContext.from_defaults(persist_dir=config.vector_store.dir)

    elif config.vector_store.type == "google_genai":
        logger.info("Setting up Google GenAI vector store")
        # Load the vector store for google genai
        print(
            f"Using Google GenAI vector store with project_id: {config.vector_store.project_id}, index_id: {config.vector_store.index_id}, endpoint_id: {config.vector_store.endpoint_id}, gcs_bucket: {config.vector_store.gcs_bucket}"
        )
        vector_store = VertexAIVectorStore(
            project_id=config.vector_store.project_id,
            region=config.vector_store.region,
            index_id=config.vector_store.index_id,
            endpoint_id=config.vector_store.endpoint_id,
            gcs_bucket_name=config.vector_store.gcs_bucket,
        )
        return StorageContext.from_defaults(vector_store=vector_store)
    else:
        raise ValueError(f"Unsupported vector store type: {config.vector_store.type}")
