import typing as t

from queryrewriter.types import TableResolver
from sqlglot import exp


class FakeTableResolver(TableResolver):
    """A fake table resolver for testing purposes. It applies a set of rewrite rules
    to the table names.
    """

    def __init__(self, rewrite_rules: list[t.Callable[[exp.Table], str | None]]):
        self.rewrite_rules = rewrite_rules

    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
        *,
        metadata: dict | None = None,
    ) -> dict[str, exp.Table]:
        resolved: dict[str, exp.Table] = {}
        for table_id, table in tables.items():
            rewritten = None
            for rule in self.rewrite_rules:
                rewritten = rule(table)
                if rewritten is not None:
                    break
            if rewritten is not None:
                resolved[table_id] = exp.to_table(rewritten)
        return resolved

    def set_rewrite_rules(
        self, rewrite_rules: list[t.Callable[[exp.Table], str | None]]
    ) -> None:
        """Sets the rewrite rules for the resolver."""
        self.rewrite_rules = rewrite_rules
