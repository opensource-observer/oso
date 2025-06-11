import logging

from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.ollama import Ollama

from ..util.config import AgentConfig, GoogleGenAILLMConfig, LocalLLMConfig
from ..util.errors import AgentConfigError

logger = logging.getLogger(__name__)

def create_llm(config: AgentConfig):
    """Setup the LLM for the agent depending on the configuration"""
    match config.llm:
        case LocalLLMConfig(
            ollama_model=model, ollama_url=base_url, ollama_timeout=timeout
        ):
            logger.info(f"Initializing Ollama LLM with model {config.llm.ollama_model}")
            return Ollama(
                model=model,
                base_url=base_url,
                request_timeout=timeout,
            )
        case GoogleGenAILLMConfig(api_key=api_key, model=model):
            logger.info("Initializing Google GenAI LLM")
            return GoogleGenAI(api_key=api_key, model=model)
        case _:
            raise AgentConfigError(f"Unsupported LLM type: {config.llm.type}")
