import typing as t

import pandas as pd
from llama_index.core.prompts import PromptTemplate
from oso_semantic.definition import SemanticQuery
from pydantic import BaseModel


class Event(BaseModel):
    """This is a base class for all events in the MixableWorkflow system.
    
    DO NOT USE THE Event CLASS FROM THE llama_index.core.workflow module."""
    pass


class Text2SQLGenerationEvent(Event):
    """An event that represents a text-to-SQL operation.

    The `text_input` is a natural language query, and the `generated_sql` value
    is the generated SQL query.
    """

    id: str
    input_text: str
    output_sql: str
    synthesize_response: bool
    execute_sql: bool


class SQLExecutionRequestEvent(Event):
    """An event that represents a request to execute a SQL query.

    The `input_text` is the natural language query if one exists, and the `output_sql` is the
    generated SQL query.
    """

    id: str
    input_text: str
    output_sql: str
    synthesize_response: bool


class SQLResultEvent(Event):
    """An event that represents a result of a SQL query.

    The `output_sql` is the SQL query that was executed, and the `rows` is a list
    of rows returned by the SQL query.
    """

    id: str
    input_text: str
    output_sql: str
    results: pd.DataFrame | list[dict[str, t.Any]]
    error: Exception | None = None
    synthesize_response: bool

    def is_valid(self) -> bool:
        """Check if the SQLResult is valid."""
        return self.error is None

    def result_to_str(self) -> str:
        """Convert the SQL result to a string representation."""
        if isinstance(self.results, pd.DataFrame):
            return self.results.to_string(index=False)
        else:
            return str(self.results)


class SQLResultSummaryRequestEvent(Event):
    """An event that represents a request for a summary of SQL rows result.

    The `sql_query` is the SQL query that was executed, and the `rows` is a list
    of rows returned by the SQL query.
    """

    id: str
    override_prompt: PromptTemplate | None = None
    result: SQLResultEvent


class SQLResultSummaryResponseEvent(Event):
    """An event that represents a summary response for SQL rows result.

    The `summary` is the generated summary of the SQL rows result.
    """

    id: str
    summary: str
    result: SQLResultEvent


class ExceptionEvent(Event):
    """An event that represents an exception that occurred during a workflow"""

    error: Exception

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return f"ExceptionEvent(error={self.error})"


class SemanticQueryEvent(Event):
    """An event that represents a semantic query generated from natural language input.

    The `structured_query` is the SemanticQuery object that represents the user's query
    in a structured format.
    The `input_text` is the original natural language query that was used to generate the
    structured query.
    """

    structured_query: SemanticQuery
    input_text: str
