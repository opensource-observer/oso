import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from .response import WrappedResponse


class WrappedResponseAgent(t.Protocol):
    """A wrapper for the agent that provides a consistent interface for responses from the agents
    """

    def get_agent(self) -> BaseWorkflowAgent:
        """Get the underlying agent."""
        ...

    async def run(self, *args, **kwargs) -> WrappedResponse:
        """Run the agent with the given arguments and return the response."""
        ...

    async def run_safe(self, *args, **kwargs) -> WrappedResponse:
        """Run the agent with the given arguments and return the response,
        handling errors and returning a wrapped error response."""
        ...