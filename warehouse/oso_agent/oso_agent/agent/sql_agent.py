import logging

from llama_index.core.agent.workflow import FunctionAgent

from ..tool.llm import create_llm
from ..tool.oso_mcp import create_oso_mcp_tools

#from llama_index.core.llms import ChatMessage
#from llama_index.core.memory import ChatMemoryBuffer
#from llama_index.core.tools import BaseTool, FunctionTool
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT: str = "You are a helpful assistant that can query the Open Source Observer data lake."

async def create_sql_agent(config: AgentConfig) -> FunctionAgent:
    """Create and configure the SQL agent."""

    try:
        llm = create_llm(config)

        logger.info("Creating agent tools")
        # local_tools = _create_local_tools()
        mcp_tools = await create_oso_mcp_tools(config)
        tools = mcp_tools
        logger.info(f"Created {len(tools)} total tools")

        logger.info("Initializing ReAct agent")
        return FunctionAgent(
            tools=tools,
            llm=llm,
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