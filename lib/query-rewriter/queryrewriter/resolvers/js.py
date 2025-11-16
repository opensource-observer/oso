# Resolve using a JavaScript provided table resolver
import typing as t

from queryrewriter.types import TableResolverProtocol

JSResolverCallable = t.Callable[[t.List[str]], t.Awaitable[t.Dict[str, t.Any]]]


class JSResolver(TableResolverProtocol):
    def __init__(self, js_resolver: JSResolverCallable):
        self.js_resolver = js_resolver

    async def resolve_tables(self, tables: t.List[str]) -> t.Dict[str, t.Any]:
        return await self.js_resolver(tables)
