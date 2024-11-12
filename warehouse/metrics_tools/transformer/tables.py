"""Transforms table references from an execution context
"""

import typing as t

from sqlglot import exp
from sqlmesh.core.context import ExecutionContext
from .base import Transform


class ExecutionContextTableTransform(Transform):
    def __init__(
        self,
        context: ExecutionContext,
    ):
        self._context = context

    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        context = self._context

        def transform_tables(node: exp.Expression):
            if not isinstance(node, exp.Table):
                return node
            table_name = f"{node.db}.{node.this.this}"
            try:
                actual_table_name = context.table(table_name)
            except KeyError:
                return node
            table_kwargs = {}
            if node.alias:
                table_kwargs["alias"] = node.alias
            return exp.to_table(actual_table_name, **table_kwargs)

        transformed_expressions = []
        for expression in query:
            transformed = expression.transform(transform_tables)
            transformed_expressions.append(transformed)
        return transformed_expressions
