import typing as t

from llama_index.core.workflow import Context
from llama_index.core.workflow.handler import WorkflowHandler
from metrics_tools.semantic.definition import SemanticQuery
from pydantic import BaseModel, Field

from .sql_query import SqlQuery


class ErrorResponse(BaseModel):
    type: t.Literal["error"] = "error"

    message: str = Field(
        description="Error message from the agent."
    )

    details: str = Field(
        default="",
        description="Optional details about the error, if available."
    )

class StrResponse(BaseModel):
    type: t.Literal["str"] = "str"

    blob: str = Field(
        description="A string response from the agent, typically used for simple text responses."
    )

class SemanticResponse(BaseModel):
    type: t.Literal["semantic"] = "semantic"

    query: SemanticQuery

class SqlResponse(BaseModel):
    type: t.Literal["sql"] = "sql"

    query: SqlQuery

ResponseType = t.Union[
    StrResponse,
    SemanticResponse,
    SqlResponse,
    ErrorResponse
]

class WrappedResponse:
    """A wrapper for the response from an agent"""
    _response: ResponseType
    _handler: WorkflowHandler

    def __init__(self, *, handler: WorkflowHandler, response: ResponseType):
        self._handler = handler
        self._response = response

    def ctx(self) -> Context:
        """Get the context of the workflow handler."""

        assert self._handler.ctx is not None, "Workflow handler context is not set."
        return self._handler.ctx
    
    @property
    def response(self) -> ResponseType:
        """Get the response from the agent."""
        return self._response


