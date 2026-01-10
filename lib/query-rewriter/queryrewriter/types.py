import abc

from pydantic import BaseModel
from sqlglot import exp


class TableResolver(abc.ABC):
    @abc.abstractmethod
    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
        *,
        metadata: dict | None = None,
    ) -> dict[str, exp.Table]:
        """Given a list of table names, resolve them to a different table
        expression.

        Args:
            tables: List of table names to resolve.
            metadata: Optional metadata that can be used during resolution.
        Returns:
            A dictionary mapping the original table names to their resolved names.
        """
        ...


class RewriteResponse(BaseModel):
    rewritten_query: str
    tables: dict[str, str]
