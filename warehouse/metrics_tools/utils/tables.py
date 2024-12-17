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


def resolve_table_name(
    context: ExecutionContext, table: exp.Table
) -> t.Tuple[str, str]:
    table_name_parts = map(resolve_identifier_or_string, table.parts)
    table_name_parts = filter(None, table_name_parts)
    table_fqn = ".".join(table_name_parts)

    return (table_fqn, context.table(table_fqn))


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
    tables_map = resolve_table_map_from_scope(context, scope)

    return tables_map
