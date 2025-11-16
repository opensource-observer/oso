# Resolve using a JavaScript provided table resolver
import typing as t

from queryrewriter.types import TableResolver

JSResolverCallable = t.Callable[[t.List[str]], t.Awaitable[t.Dict[str, t.Any]]]


class JSResolver(TableResolver):
    def __init__(self, js_resolver: JSResolverCallable):
        self.js_resolver = js_resolver

    async def resolve_tables(self, tables: t.List[str]) -> t.Dict[str, t.Any]:
        return await self.js_resolver(tables)
