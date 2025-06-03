import logging

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from ..prompts.system import SYSTEM_PROMPT
from ..tool.llm import create_llm
from ..tool.oso_mcp_tools import create_oso_mcp_tools
from ..util.config import AgentConfig
from ..util.errors import AgentConfigError
from .decorator import wrapped_agent

logger = logging.getLogger(__name__)
#SYSTEM_PROMPT: str = "You are a helpful assistant that can query the Open Source Observer data lake."

@wrapped_agent()
async def create_react_mcp_agent(config: AgentConfig) -> BaseWorkflowAgent:
    """Create and configure the ReAct agent."""

    try:
        logger.info("Creating react_mcp agent")
        llm = create_llm(config)
        # local_tools = _create_local_tools()
        mcp_tools = await create_oso_mcp_tools(config)
        tools = mcp_tools
        logger.info(f"Created {len(tools)} total tools")

        logger.info("Initializing ReAct agent")
        return ReActAgent(
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