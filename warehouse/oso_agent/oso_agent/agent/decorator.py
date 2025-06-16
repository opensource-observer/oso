import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from oso_agent.types.response import StrResponse, ResponseType 

from ..util.config import AgentConfig
from .base import GenericWrappedAgent, ResponseWrapper


def str_response_wrapper(response: t.Any) -> ResponseType:
    """Wrap a string response in a WrappedAgentResponse."""
    return StrResponse(blob=str(response))
    
AgentFactory = t.Callable[[AgentConfig], t.Awaitable[BaseWorkflowAgent]]

def wrapped_agent(wrapper_function: ResponseWrapper | None = None):
    """A decorator to wrap an agent's run method with a response wrapper."""

    if not wrapper_function:
        wrapper_function = str_response_wrapper

    def _factory(decorated: AgentFactory) -> t.Callable[[AgentConfig], t.Awaitable[GenericWrappedAgent]]:
        async def wrapper(config: AgentConfig) -> GenericWrappedAgent:
            """Wrapper function to call the agent's run method."""
            agent = await decorated(config)
            return GenericWrappedAgent(agent, wrapper_function)
        return wrapper
    return _factory
