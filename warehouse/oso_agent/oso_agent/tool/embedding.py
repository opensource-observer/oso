
import logging

from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding

from ..util.config import AgentConfig, GoogleGenAILLMConfig, LocalLLMConfig
from ..util.errors import AgentConfigError

logger = logging.getLogger(__name__)

def create_embedding(config: AgentConfig):
    """Setup the embedding model depending on the configuration"""
    match config.llm:
        case LocalLLMConfig(
            ollama_embedding=embedding, ollama_url=base_url, ollama_timeout=timeout
        ):
            logger.info(f"Initializing Ollama embedding model {config.llm.ollama_model}")
            return OllamaEmbedding(
                model_name=embedding,
                base_url=base_url,
                request_timeout=timeout,
            )
        case GoogleGenAILLMConfig(api_key=api_key, embedding=embedding):
            logger.info("Initializing Google GenAI embedding model")
            return GoogleGenAIEmbedding(
                api_key=api_key,
                model_name=embedding,
                embed_batch_size=100,
            )
        case _:
            raise AgentConfigError(f"Unsupported LLM type: {config.llm.type}")
