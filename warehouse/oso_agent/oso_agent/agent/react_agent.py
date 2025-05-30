import logging

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from ..tool.llm import create_llm
from ..tool.oso_mcp_tools import create_oso_mcp_tools
from ..types.sql_query import SqlQuery

#from llama_index.core.llms import ChatMessage
#from llama_index.core.memory import ChatMemoryBuffer
#from llama_index.core.tools import BaseTool, FunctionTool
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError
from .decorator import wrapped_agent

logger = logging.getLogger(__name__)

#SYSTEM_PROMPT: str = "You are a helpful assistant that can query the Open Source Observer data lake."
SYSTEM_PROMPT: str = """
You are a text to SQL translator.
You will be given a natural language query and you should return a SQL query
that is equivalent to the natural language query.

Make sure that your response only contains a single valid SQL query.
Do not include any other text or explanation.

Make sure that any tables or columns you reference in your SQL query actually exist in the database.
"""

@wrapped_agent()
async def create_react_agent(config: AgentConfig) -> BaseWorkflowAgent:
    """Create and configure the ReAct agent."""

    try:
        llm = create_llm(config)
        sllm = llm.as_structured_llm(SqlQuery)

        logger.info("Creating agent tools")
        # local_tools = _create_local_tools()
        mcp_tools = await create_oso_mcp_tools(config, [
            "list_tables",
            "get_table_schema",
            "get_sample_queries"
        ])
        tools = mcp_tools
        logger.info(f"Created {len(tools)} total tools")

        logger.info("Initializing ReAct agent")
        return ReActAgent(
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