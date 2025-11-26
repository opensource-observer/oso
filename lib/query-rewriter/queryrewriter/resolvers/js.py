# Resolve using a JavaScript provided table resolver
import typing as t

from queryrewriter.types import TableResolver
from sqlglot import exp

JSResolverCallable = t.Callable[[t.List[str], dict], t.Awaitable[t.Dict[str, str]]]


def table_to_str(table: exp.Table) -> str:
    assert table.name is not None, "Table must have a name"
    if table.catalog and table.db:
        return f"{table.catalog}.{table.db}.{table.name}"
    elif table.db:
        return f"{table.db}.{table.name}"
    else:
        return table.name


class JSResolver(TableResolver):
    """For use within pyodide environments. A javascript function is provided that
    takes a list of table references and returns the resolved table fqns.
    """

    def __init__(self, js_resolver: JSResolverCallable):
        self.js_resolver = js_resolver

    async def resolve_tables(
        self,
        tables: dict[str, exp.Table],
        *,
        metadata: dict | None = None,
    ) -> dict[str, exp.Table]:
        """The table dict passed into this function could have tables that are not FQNs.
        It is also possible that this has been preprocessed by other resolvers. The key
        is intended to be the identifier used by the caller to identify the table, so we
        need to maintain that mapping. We convert each table to a string representation,
        pass that to the JS resolver, and then map back the results to the original keys.
        """

        metadata = metadata or {}
        intermediate_lookup_to_id: t.Dict[str, str] = {}
        resolved: dict[str, exp.Table] = {}
        for table_id, table in tables.items():
            lookup = table_to_str(table)
            intermediate_lookup_to_id[lookup] = table_id
        resolved_name_map = await self.js_resolver(
            list(intermediate_lookup_to_id.keys()), metadata
        )

        for intermediate_lookup, table_id in intermediate_lookup_to_id.items():
            resolved_name = resolved_name_map.get(intermediate_lookup)
            if not resolved_name:
                raise ValueError(
                    f"JS Resolver did not return a resolved name for table {table_id}:{intermediate_lookup}"
                )
            resolved[table_id] = exp.to_table(resolved_name)
        return resolved
