import typing as t
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
from llama_index.core.prompts import PromptTemplate
from llama_index.core.workflow import Event


class Text2SQLGenerationEvent(Event):
    """An event that represents a text-to-SQL operation.

    The `text_input` is a natural language query, and the `generated_sql` value
    is the generated SQL query.
    """

    id: str
    input_text: str
    output_sql: str


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


class QueryAttemptStatus(Enum):
    """Status of a query attempt in the correction loop"""

    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"


@dataclass
class QueryAttempt:
    """Represents a single attempt at generating a semantic query"""

    iteration: int
    query: str
    semantic_query: str | None = None
    generated_sql: str | None = None
    error_message: str | None = None
    error_type: str | None = None
    status: QueryAttemptStatus = QueryAttemptStatus.PENDING
    suggestions: list[str] = field(default_factory=list)


@dataclass
class CorrectionContext:
    """Context information to help with query correction"""

    available_models: list[str] = field(default_factory=list)
    available_dimensions: dict[str, list[str]] = field(default_factory=dict)
    available_measures: dict[str, list[str]] = field(default_factory=dict)
    available_relationships: dict[str, list[str]] = field(default_factory=dict)
    previous_errors: list[str] = field(default_factory=list)


class SemanticQueryRequestEvent(Event):
    """Event requesting semantic query processing with error correction loop"""

    id: str
    query: str
    max_iterations: int = 5


class SemanticQueryAttemptEvent(Event):
    """Event representing a single query attempt"""

    id: str
    attempt: QueryAttempt
    context: CorrectionContext


class SemanticQueryResponseEvent(Event):
    """Event containing the final result of semantic query processing"""

    id: str
    attempts: list[QueryAttempt]
    final_sql: str | None = None
    success: bool = False


@dataclass
class SemanticQueryErrorEvent(Event):
    """Event for semantic query errors with correction suggestions"""

    id: str
    error: Exception
    error_type: str
    suggestions: list[str] = field(default_factory=list)
    iteration: int = 1
