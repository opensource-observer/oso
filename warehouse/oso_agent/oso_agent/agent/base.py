import typing as t

from llama_index.core.agent.workflow.base_agent import BaseWorkflowAgent
from opentelemetry import trace
from oso_agent.types.response import WrappedResponse

from ..types import ErrorResponse, ResponseType

ResponseWrapper = t.Callable[[t.Any], ResponseType]

tracer = trace.get_tracer(__name__)


class GenericWrappedAgent:
    def __init__(self, agent: BaseWorkflowAgent, response_wrapper: ResponseWrapper):
        self._agent = agent
        self._response_wrapper = response_wrapper

    def get_agent(self) -> BaseWorkflowAgent:
        return self._agent

    async def run(self, *args, **kwargs) -> WrappedResponse:
        """Run the agent with the given arguments and return the response."""
        with tracer.start_as_current_span("run"):
            handler = self._agent.run(*args, **kwargs)
            raw_response = await handler

            return WrappedResponse(
                handler=handler, response=self._response_wrapper(raw_response)
            )

    async def run_safe(self, *args, **kwargs) -> WrappedResponse:
        """Run the agent with the given arguments and return the response,
        handling errors and returning a wrapped error response."""
        handler = self._agent.run(*args, **kwargs)
        with tracer.start_as_current_span("run"):
            try:
                raw_response = await handler
            except Exception as e:
                # Handle exceptions and return a wrapped error response
                return WrappedResponse(
                    handler=handler, response=self._wrap_error(e)
                )
            return WrappedResponse(
                handler=handler, response=self._response_wrapper(raw_response)
            )

    def _wrap_error(self, error: Exception) -> ResponseType:
        """Wrap an error into a response."""
        response = ErrorResponse(
            message=str(error),
        )
        return response
