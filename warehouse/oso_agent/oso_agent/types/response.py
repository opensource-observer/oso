import typing as t

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

ResponseTypes = t.Union[
    StrResponse,
    SemanticResponse,
    SqlResponse,
    ErrorResponse
]

class WrappedResponse(BaseModel):
    """A wrapper for the response from an agent"""

    response: ResponseTypes = Field(discriminator="type")

