import typing as t
from dataclasses import dataclass

from metrics_tools.transformer.base import Transform
from metrics_tools.transformer.qualify import QualifyTransform
from sqlglot import exp
from sqlmesh.core.dialect import parse


@dataclass(kw_only=True)
class SQLTransformer:
    """The sql transformer.

    This defines a process for sql transformation. Given an ordered list of Transforms
    """

    transforms: t.List[Transform]
    disable_qualify: bool = False

    def transform(
        self, query: str | t.List[exp.Expression], dialect: str | None = None
    ):
        if isinstance(query, str):
            transformed = parse(query, default_dialect=dialect)
        else:
            transformed = query
        # Qualify all
        # transformed = list(map(qualify, transformed))
        if not self.disable_qualify:
            transformed = QualifyTransform()(transformed)

        for transform in self.transforms:
            transformed = transform(transformed)
            # print("transformed")
            # for expr in transformed:
            #     print(expr.sql(dialect="trino"))
        return transformed
