import abc


class TableResolver(abc.ABC):
    @abc.abstractmethod
    async def resolve_tables(self, tables: list[str]) -> dict[str, str]:
        """Given a list of table names, resolve them to their full names.

        Args:
            tables: List of table names to resolve.
        Returns:
            A dictionary mapping the original table names to their resolved names.
        """
        ...
