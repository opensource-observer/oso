import abc
import typing as t
from dataclasses import dataclass

from sqlglot import exp
from sqlmesh.core.dialect import parse
from sqlglot.optimizer.qualify import qualify


class Transform(abc.ABC):
    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        raise NotImplementedError("transformation not implemented")


@dataclass(kw_only=True)
class SQLTransformer:
    """The sql transformer.

    This defines a process for sql transformation. Given an ordered list of Transforms
    """

    transforms: t.List[Transform]

    def transform(self, query: str | t.List[exp.Expression]):
        if isinstance(query, str):
            transformed = parse(query)
        else:
            transformed = query
        # Qualify all
        transformed = list(map(qualify, transformed))

        for transform in self.transforms:
            transformed = transform(transformed)
        return transformed
