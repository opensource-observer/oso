import abc
import typing as t

from sqlglot import exp


class Transform(abc.ABC):
    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        raise NotImplementedError("transformation not implemented")
