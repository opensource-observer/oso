"""
SQLMesh + SQLGlot related tools
"""

from typing import Any, Dict

from sqlmesh.core.dialect import parse_one
from sqlmesh.core.renderer import ExpressionRenderer


class SchemaResolver:
    def resolve_table(self, table_name: str) -> Dict[str, Any]:
        raise NotImplementedError("resolve_table not implemented")

    def all_schemas(self) -> Dict[str, Any]:
        raise NotImplementedError("all_schemas not implemented")


class DictResolver(SchemaResolver):
    def __init__(self, d: Dict[str, Dict[str, Any]]):
        self._dict = d

    def resolve_table(self, table_name: str):
        return self._dict[table_name]

    def all_schemas(self):
        return self._dict


def render_with_sqlmesh(
    query: str, *, dialect: str, schema_loader: SchemaResolver, **render_vars
):
    parsed_query = parse_one(query, dialect=dialect)
    rendered = ExpressionRenderer(
        parsed_query, dialect, [], schema=schema_loader.all_schemas()
    ).render(**render_vars)
    if not rendered:
        raise Exception("Nothing rendered")
    if len(rendered) > 1:
        raise Exception("Unexpected number of returned expressions")
    return rendered[0]


def render_sqlmesh(query: str, *, dialect: str, **render_vars):
    parsed_query = parse_one(query, dialect=dialect)
    rendered = ExpressionRenderer(parsed_query, dialect, []).render(**render_vars)
    if not rendered:
        raise Exception("Nothing rendered")
    if len(rendered) > 1:
        raise Exception("Unexpected number of returned expressions")
    return rendered[0]
