import typing as t

from sqlglot import exp
from sqlmesh import ExecutionContext
from sqlmesh.core.dialect import parse_one


def resolve_identifier_or_string(i: exp.Expression | str) -> t.Optional[str]:
    if isinstance(i, str):
        return i
    if isinstance(i, (exp.Identifier, exp.Literal)):
        return i.this
    return None


def create_dependent_tables_map(
    context: ExecutionContext, query_str: str
) -> t.Dict[str, str]:
    query = parse_one(query_str)
    tables = query.find_all(exp.Table)

    tables_map: t.Dict[str, str] = {}

    for table in tables:
        table_name_parts = map(resolve_identifier_or_string, table.parts)
        table_name_parts = filter(None, table_name_parts)
        table_fqn = ".".join(table_name_parts)

        tables_map[table_fqn] = context.table(table_fqn)

    return tables_map
