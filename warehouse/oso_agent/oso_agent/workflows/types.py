import pandas as pd
from llama_index.core.workflow import Event


class Mixin:
    """A base mixin class for agent workflows.

    """
    pass


class Text2SQLGenerationEvent(Event):
    """An event that represents a text-to-SQL operation.

    The `text_input` is a natural language query, and the `generated_sql` value
    is the generated SQL query.
    """

    text_input: str
    generated_sql: str


class SQLDataFrameResultEvent(Event):
    """An event that represents a dataframe result

    The `df` is a pandas DataFrame containing the results of the SQL query. The
    `sql_query` is the SQL query that was executed.
    """

    sql_query: str
    result: pd.DataFrame
    error: Exception | None = None

    def is_valid(self) -> bool:
        """Check if the SQLDataFrameResult is valid."""
        return self.error is None
    
    @property
    def df(self):
        """Alias for the result DataFrame."""
        return self.result
        

class SQLDataFrameResultSummaryRequestEvent(Event):
    """An event that represents a request for a summary of a SQL DataFrame result.

    The `sql_query` is the SQL query that was executed, and the `df` is the
    pandas DataFrame containing the results of the SQL query.
    """

    prompt: str
    result: SQLDataFrameResultEvent

class SQLDataFrameResultSummaryResponseEvent(Event):
    """An event that represents a summary response for a SQL DataFrame result.

    The `summary` is the generated summary of the SQL DataFrame result.
    """

    summary: str
    result: SQLDataFrameResultEvent