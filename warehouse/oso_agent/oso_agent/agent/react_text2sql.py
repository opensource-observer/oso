import logging

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from llama_index.core.tools import QueryEngineTool
from oso_agent.tool.storage_context import setup_storage_context

from ..prompts.system import SYSTEM_PROMPT
from ..tool.embedding import create_embedding
from ..tool.llm import create_llm
from ..tool.oso_text2sql import create_oso_query_engine

# from ..tool.oso_mcp import create_oso_mcp_tools
# from ..types.response import SqlResponse, WrappedResponse
# from ..types.sql_query import SqlQuery
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError
from .decorator import wrapped_agent

logger = logging.getLogger(__name__)

# def as_sql_response(raw_response: t.Any) -> WrappedResponse:
#    query = SqlQuery.model_validate_json(str(raw_response))
#    response = SqlResponse(query=query)
#    return WrappedResponse(response=response)


@wrapped_agent()
async def create_react_text2sql_agent(config: AgentConfig) -> BaseWorkflowAgent:
    """Create and configure the agent."""

    try:
        # Create a structured LLM for generating SQL queries
        logger.info("Initializing function_text2sql agent")
        llm = create_llm(config)
        embedding = create_embedding(config)

        storage_context = setup_storage_context(config, embed_model=embedding)

        query_engine = await create_oso_query_engine(
            config,
            storage_context,
            llm,
            embedding,
        )
        tools = [
            QueryEngineTool.from_defaults(
                query_engine,
                name="oso_query_engine",
                description="Query the OSO data lake for structured data.",
            ),
        ]

        return ReActAgent(
            tools=tools,
            llm=llm,
            system_prompt=SYSTEM_PROMPT,
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise AgentConfigError(f"Failed to create agent: {e}") from e
