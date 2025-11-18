import typing as t

from queryrewriter.types import TableResolver


class FakeTableResolver(TableResolver):
    def __init__(self, rewrite_rules: list[t.Callable[[str], str | None]]):
        self.rewrite_rules = rewrite_rules

    async def resolve_tables(self, tables: list[str]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for table in tables:
            rewritten = None
            for rule in self.rewrite_rules:
                rewritten = rule(table)
                if rewritten is not None:
                    break
            if rewritten is not None:
                resolved[table] = rewritten
        return resolved
