import copy
import typing as t

from sqlglot import exp
from sqlglot.optimizer.scope import Scope, build_scope
from sqlmesh import ExecutionContext
from sqlmesh.core.dialect import parse_one


def resolve_identifier_or_string(i: exp.Expression | str) -> t.Optional[str]:
    if isinstance(i, str):
        return i
    if isinstance(i, (exp.Identifier, exp.Literal)):
        return i.this
    return None


def resolve_table_fqn(table: exp.Table) -> str:
    table_name_parts = map(resolve_identifier_or_string, table.parts)
    table_name_parts = filter(None, table_name_parts)
    return ".".join(table_name_parts)


def resolve_table_name(
    context: ExecutionContext, table: exp.Table
) -> t.Tuple[str, str]:
    table_fqn = resolve_table_fqn(table)

    return (table_fqn, context.resolve_table(table_fqn))


def list_query_table_dependencies_from_str(query: str) -> t.Set[str]:
    return list_query_table_dependencies(parse_one(query), {})


def list_query_table_dependencies(
    query: exp.Expression, parent_ctes: t.Dict[str, exp.Expression]
) -> t.Set[str]:
    tables: t.Set[str] = set()
    cte_lookup = copy.deepcopy(parent_ctes)

    assert isinstance(
        query, (exp.Select, exp.Union)
    ), f"Unsupported query type {type(query)}"

    # Lookup ctes
    for cte in query.ctes:
        cte_lookup[cte.alias] = cte.this

    if isinstance(query, exp.Union):
        tables = tables.union(list_query_table_dependencies(query.this, cte_lookup))
        tables = tables.union(
            list_query_table_dependencies(query.expression, cte_lookup)
        )

    else:
        table_sources: t.List[exp.Expression] = [query.args["from"]]
        joins = query.args.get("joins", [])
        table_sources.extend(joins)
        for source in table_sources:
            for table in source.find_all(exp.Table):
                table_fqn = resolve_table_fqn(table)
                if table_fqn in cte_lookup:
                    continue
                tables.add(table_fqn)

    # Recurse into the ctes
    for cte in query.ctes:
        tables = tables.union(list_query_table_dependencies(cte.this, cte_lookup))

    return tables


def resolve_table_map_from_scope(
    context: ExecutionContext, scope: Scope
) -> t.Dict[str, str]:
    current_tables_map = {}
    for source_name, source in scope.sources.items():
        if isinstance(source, exp.Table):
            local_name, actual_name = resolve_table_name(context, source)
            current_tables_map[local_name] = actual_name
        elif isinstance(source, Scope):
            parent_tables_map = resolve_table_map_from_scope(context, source)
            current_tables_map.update(parent_tables_map)
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")
    return current_tables_map


def create_dependent_tables_map(
    context: ExecutionContext, query_str: str
) -> t.Dict[str, str]:
    query = parse_one(query_str)
    scope = build_scope(query)
    if not scope:
        raise ValueError("Failed to build scope")
    # tables_map = resolve_table_map_from_scope(context, scope)
    tables = list_query_table_dependencies(query, {})
    tables_map = {table: context.resolve_table(table) for table in tables}

    return tables_map
