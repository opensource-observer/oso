"""Transforms table references from an execution context
"""

import logging
import typing as t

from sqlglot import exp
from sqlmesh.core.context import ExecutionContext

from .base import Transform

logger = logging.getLogger(__name__)


class TableTransform(Transform):
    def transform_table_name(self, table: exp.Table) -> exp.Table | None:
        raise NotImplementedError("transform table not implemeented")

    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        def transform_tables(node: exp.Expression):
            if not isinstance(node, exp.Table):
                return node
            actual_table = self.transform_table_name(node)
            if not actual_table:
                return node
            if node.alias:
                actual_table = actual_table.as_(node.alias)
            return actual_table

        transformed_expressions = []
        for expression in query:
            transformed = expression.transform(transform_tables)
            transformed_expressions.append(transformed)
        return transformed_expressions


class MapTableTransform(TableTransform):
    def __init__(self, map: t.Dict[str, str]):
        self._map = map

    def transform_table_name(self, table: exp.Table) -> exp.Table | None:
        table_name = f"{table.db}.{table.this.this}"
        actual_name = self._map.get(table_name, None)
        if actual_name:
            return exp.to_table(actual_name)
        return None


class ExecutionContextTableTransform(TableTransform):
    def __init__(
        self,
        context: ExecutionContext,
    ):
        self._context = context

    def transform_table_name(self, table: exp.Table) -> exp.Table | None:
        table_name = f"{table.db}.{table.this.this}"
        try:
            logger.debug(
                f"Transforming tables for query {self._context.resolve_table(table_name)}"
            )
            return exp.to_table(self._context.resolve_table(table_name))
        except KeyError:
            return None
