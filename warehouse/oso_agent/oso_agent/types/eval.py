import typing as t

from oso_agent.eval.valid_sql import is_valid_sql
from oso_agent.types.response import ResponseType
from pydantic import BaseModel, Field


# struct
class ExampleResult(BaseModel):
    agent_response: ResponseType | None = None
    actual_sql_query: str = ""
    order_matters: bool = False
    expected_sql_query: str = ""
    actual_sql_result: list[dict[str, t.Any]] = Field(default_factory=list)
    is_valid_sql_result: bool = False
    expected_sql_result: list[dict[str, t.Any]] = Field(default_factory=list)

    @property
    def is_valid_sql(self) -> bool:
        """
        Returns True if the actual SQL query is valid, i.e., it does not contain any errors.
        """
        return is_valid_sql(self.actual_sql_query)

    def results_to_list_tuple(self, rows: list[dict[str, t.Any]]) -> list[tuple]:
        if len(rows) == 0:
            return []
        columns = list(rows[0].keys())
        # treat the top row as column names
        tuples = [tuple(columns)] + [tuple(row[col] for col in columns) for row in rows]
        return tuples
    
    def actual_results_to_list_tuple(self) -> list[tuple]:
        return self.results_to_list_tuple(self.actual_sql_result)
    
    def expected_results_to_list_tuple(self) -> list[tuple]:
        return self.results_to_list_tuple(self.expected_sql_result)
    