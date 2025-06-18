import typing as t
import pandas as pd
from llama_index.core.workflow import Event
from llama_index.core.prompts import PromptTemplate


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