import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent

from ..types import ErrorResponse, WrappedResponse

ResponseWrapper = t.Callable[[t.Any], WrappedResponse]

class GenericWrappedAgent:
    def __init__(self, agent: BaseWorkflowAgent, response_wrapper: ResponseWrapper):
        self._agent = agent
        self._response_wrapper = response_wrapper

    def get_agent(self) -> BaseWorkflowAgent:
        return self._agent
    
    async def run(self, *args, **kwargs) -> WrappedResponse:
        """Run the agent with the given arguments and return the response."""
        raw_response = await self._agent.run(*args, **kwargs)
        return self._response_wrapper(raw_response)
    
    async def run_safe(self, *args, **kwargs) -> WrappedResponse:
        """Run the agent with the given arguments and return the response,
        handling errors and returning a wrapped error response."""
        try:
            return await self.run(*args, **kwargs)
        except Exception as e:
            # Handle exceptions and return a wrapped error response
            return self._wrap_error(e)
        
    def _wrap_error(self, error: Exception) -> WrappedResponse:
        """Wrap an error into a response."""
        response = ErrorResponse(
            message=str(error),
        )
        return WrappedResponse(response=response)