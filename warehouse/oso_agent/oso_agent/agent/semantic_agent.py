import logging

# from llama_index.core.agent.workflow import FunctionAgent
import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

# from ..tool.oso_mcp import create_oso_mcp_tools
from oso_semantic.definition import SemanticQuery
from oso_semantic.testing import setup_registry

from ..tool.llm import create_llm
from ..types.response import ResponseType, SemanticResponse
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError
from .basic_agent import BasicAgent
from .decorator import wrapped_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT: str = """
You are a text to SemanticQuery translator. You will be given a natural language
query and you should return a valid SemanticQuery object that represents the
query based on a given semantic model.

Make sure that your response only contains only the correct SemanticQuery object.

The Semantic Model is as follows
---

"""

def as_semantic_response(raw_response: t.Any) -> ResponseType:
    """Wrap a SemanticQuery response in a WrappedAgentResponse."""
    query = SemanticQuery.model_validate_json(str(raw_response))
    response = SemanticResponse(query=query)
    return response


@wrapped_agent(as_semantic_response)
async def create_semantic_agent(config: AgentConfig) -> BaseWorkflowAgent:
    """Create and configure the SQL agent."""

    semantic_registry = setup_registry()
    prompt = SYSTEM_PROMPT + semantic_registry.describe()

    try:
        # Create a structured LLM for generating SQL queries
        llm = create_llm(config)
        sllm = llm.as_structured_llm(SemanticQuery)
        tools = []

        logger.info("Initializing Semantic agent")
        return BasicAgent(
            tools=tools,
            llm=sllm,
            system_prompt=prompt,
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise AgentConfigError(f"Failed to create agent: {e}") from e
