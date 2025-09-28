import typing as t

import pandas as pd
from llama_index.core.prompts import PromptTemplate
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.workflow import Event
from oso_agent.tool.oso_sql_db import OsoSqlDatabase
from oso_semantic.definition import SemanticQuery


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
    remaining_tries: int
    error_context: list[str] = []


class SQLExecutionRequestEvent(Event):
    """An event that represents a request to execute a SQL query.

    The `input_text` is the natural language query, and the `output_sql` is the
    generated SQL query.
    """

    id: str
    input_text: str
    output_sql: str
    synthesize_response: bool
    remaining_tries: int
    error_context: list[str] = []


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
    The `remaining_tries` is the number of remaining attempts to generate a valid query.
    The `error_context` accumulates error messages from previous attempts to provide
    better context to the LLM for retry attempts.
    """

    id: str
    structured_query: SemanticQuery
    input_text: str
    remaining_tries: int = 5
    error_context: list[str] = []
    synthesize_response: bool = True
    execute_sql: bool = True


class RetrySemanticQueryEvent(Event):
    """An event that represents a retry attempt for a semantic query generation.

    The `input_text` is the original natural language query that was used to generate the
    structured query.
    The `error` is the error that occurred during the previous attempt.
    The `remaining_tries` is the number of remaining attempts.
    The `error_context` accumulates error messages from previous attempts to provide
    better context to the LLM for retry attempts.
    """

    id: str
    input_text: str
    error: Exception
    remaining_tries: int
    error_context: list[str] = []
    synthesize_response: bool = True
    execute_sql: bool = True


class StartQueryEngineEvent(Event):
    """Event to start the QueryEngine workflow steps."""

    id: str
    input_text: str
    synthesize_response: bool = True
    execute_sql: bool = True


class SchemaAnalysisEvent(Event):
    """Event carrying schema analysis results."""

    id: str
    input_text: str
    sql_database: OsoSqlDatabase
    relevant_tables: list[str]
    synthesize_response: bool = True
    execute_sql: bool = True


class TableSelectionEvent(Event):
    """Event carrying table selection results for semantic query."""

    id: str
    input_text: str
    selected_models: list[str]
    filtered_registry_description: str
    synthesize_response: bool = True
    execute_sql: bool = True


class RowContextEvent(Event):
    """Event carrying row context retrieval results."""

    id: str
    input_text: str
    sql_database: OsoSqlDatabase
    relevant_tables: list[str]
    row_retrievers: dict[str, BaseRetriever]
    synthesize_response: bool = True
    execute_sql: bool = True
