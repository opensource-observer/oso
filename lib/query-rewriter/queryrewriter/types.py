import abc

from sqlglot import exp


class TableResolver(abc.ABC):
    @abc.abstractmethod
    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
    ) -> dict[str, exp.Table]:
        """Given a list of table names, resolve them to a different table
        expression.

        Args:
            tables: List of table names to resolve.
        Returns:
            A dictionary mapping the original table names to their resolved names.
        """
        ...
