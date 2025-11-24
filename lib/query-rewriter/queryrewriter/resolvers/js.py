# Resolve using a JavaScript provided table resolver
import typing as t

from queryrewriter.types import TableResolver
from sqlglot import exp

JSResolverCallable = t.Callable[[t.List[str], dict], t.Awaitable[t.Dict[str, str]]]


class JSResolver(TableResolver):
    """For use within pyodide environments. A javascript function is provided that
    takes a list of fully qualified table names and returns a mapping of input table
    names to resolved table names.
    """

    def __init__(self, js_resolver: JSResolverCallable):
        self.js_resolver = js_resolver

    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
        *,
        metadata: dict | None = None,
    ) -> dict[str, exp.Table]:
        metadata = metadata or {}
        table_fqn_to_id: t.Dict[str, str] = {}
        resolved: dict[str, exp.Table] = {}
        for table_id, table in tables.items():
            fqn = f"{table.catalog}.{table.db}.{table.name}"
            table_fqn_to_id[fqn] = table_id
        resolved_name_map = await self.js_resolver(
            list(table_fqn_to_id.keys()), metadata
        )
        for input_fqn, table_id in table_fqn_to_id.items():
            resolved[table_id] = exp.to_table(
                resolved_name_map.get(input_fqn, input_fqn)
            )
        return resolved
