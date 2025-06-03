import logging
from typing import List, Sequence

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from llama_index.core.agent.workflow.single_agent_workflow import SingleAgentRunnerMixin
from llama_index.core.agent.workflow.workflow_events import (
    AgentInput,
    AgentOutput,
    AgentStream,
    ToolCallResult,
)
from llama_index.core.base.llms.types import ChatResponse
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import BaseMemory
from llama_index.core.tools import AsyncBaseTool
from llama_index.core.workflow import Context

logger = logging.getLogger(__name__)

class BasicAgent(SingleAgentRunnerMixin, BaseWorkflowAgent):
    """Basic agent implementation. This is a fork of FunctionAgent stripped of tool access."""

    scratchpad_key: str = "scratchpad"

    async def take_step(
        self,
        ctx: Context,
        llm_input: List[ChatMessage],
        tools: Sequence[AsyncBaseTool],
        memory: BaseMemory,
    ) -> AgentOutput:
        """Take a single step with the basic agent."""
        scratchpad: List[ChatMessage] = await ctx.get(self.scratchpad_key, default=[])
        current_llm_input = [*llm_input, *scratchpad]

        ctx.write_event_to_stream(
            AgentInput(input=current_llm_input, current_agent_name=self.name)
        )

        response = await self.llm.astream_chat(  # type: ignore
            messages=current_llm_input,
        )
        logging.info(f"Response: {response}")
        # last_chat_response will be used later, after the loop.
        # We initialize it so it's valid even when 'response' is empty
        last_chat_response = ChatResponse(message=ChatMessage())
        async for last_chat_response in response:
            raw = (
                last_chat_response.raw.model_dump()
                if isinstance(last_chat_response.raw, BaseModel)
                else last_chat_response.raw
            )
            ctx.write_event_to_stream(
                AgentStream(
                    delta=last_chat_response.delta or "",
                    response=last_chat_response.message.content or "",
                    tool_calls=[],
                    raw=raw,
                    current_agent_name=self.name,
                )
            )

        # only add to scratchpad if we didn't select the handoff tool
        scratchpad.append(last_chat_response.message)
        await ctx.set(self.scratchpad_key, scratchpad)

        raw = (
            last_chat_response.raw.model_dump()
            if isinstance(last_chat_response.raw, BaseModel)
            else last_chat_response.raw
        )
        return AgentOutput(
            response=last_chat_response.message,
            tool_calls=[],
            raw=raw,
            current_agent_name=self.name,
        )

    async def handle_tool_call_results(
        self, ctx: Context, results: List[ToolCallResult], memory: BaseMemory
    ) -> None:
        """Handle tool call results for function calling agent."""

    async def finalize(
        self, ctx: Context, output: AgentOutput, memory: BaseMemory
    ) -> AgentOutput:
        """Finalize the basic agent.

        Adds all in-progress messages to memory.
        """
        scratchpad: List[ChatMessage] = await ctx.get(self.scratchpad_key, default=[])
        await memory.aput_messages(scratchpad)

        # reset scratchpad
        await ctx.set(self.scratchpad_key, [])

        return output
    