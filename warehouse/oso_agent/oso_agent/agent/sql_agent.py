import logging
import typing as t

#from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from ..tool.llm import create_llm
from ..types.response import SqlResponse, WrappedResponse

#from ..tool.oso_mcp import create_oso_mcp_tools
from ..types.sql_query import SqlQuery
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError
from .basic_agent import BasicAgent
from .decorator import wrapped_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT: str = """
You are a text to SQL translator.
You will be given a natural language query and you should return a SQL query
that is equivalent to the natural language query.

Make sure that your response only contains a single valid SQL query.
Do not include any other text or explanation.
"""

    
def as_sql_response(raw_response: t.Any) -> WrappedResponse:
    query = SqlQuery.model_validate_json(raw_response)
    response = SqlResponse(query=query)
    return WrappedResponse(response=response)


@wrapped_agent(as_sql_response)
async def create_sql_agent(config: AgentConfig) -> BaseWorkflowAgent:
    """Create and configure the SQL agent."""

    try:
        # Create a structured LLM for generating SQL queries
        llm = create_llm(config)
        sllm = llm.as_structured_llm(SqlQuery)
        tools = []

        logger.info("Initializing SQL agent")
        return BasicAgent(
            tools=tools,
            llm=sllm,
            system_prompt=SYSTEM_PROMPT,
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise AgentConfigError(f"Failed to create agent: {e}") from e

#    async def run(
#        self, query: str, chat_history: list[ChatMessage] | None = None
#    ) -> str:
#        """Run a query through the agent."""
#
#        chat_buffer = ChatMemoryBuffer(token_limit=1000000)
#
#        logger.info(f"Running query: {query}")
#        chat_history = chat_history or []
#
#        response = await self.react_agent.run(
#            query, chat_history=chat_history, memory=chat_buffer
#        )
#        return str(response)
#