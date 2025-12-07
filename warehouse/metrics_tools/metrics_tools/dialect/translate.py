"""
Enables custom sql functions that can be processed into normal python objects as well as sql.
"""

import typing as t

from sqlglot import exp
from sqlmesh.core.macros import MacroEvaluator


class CustomFuncHandler[T]:
    name: str

    def to_obj(self, *args, **kwargs) -> T:
        raise NotImplementedError("to_obj not implement")

    def transform(
        self, evaluator: MacroEvaluator, context: t.Dict[str, t.Any], obj: T
    ) -> exp.Expression:
        raise NotImplementedError("transform not implemented")


class CustomFuncRegistry:
    def __init__(self):
        self._map: t.Dict[str, CustomFuncHandler] = {}

    def register(self, handler: CustomFuncHandler):
        self._map[handler.name] = handler

    def get(self, name: str):
        return self._map.get(name)

    @property
    def names(self):
        return list(self._map.keys())


def send_anonymous_to_callable[T](anon: exp.Anonymous, f: t.Callable[..., T]):
    # much of this is taken from sqlmesh.core.macros
    args = []
    kwargs = {}

    for e in anon.expressions:
        if isinstance(e, exp.PropertyEQ):
            kwargs[e.this.name] = e.expression
        else:
            if kwargs:
                raise Exception(
                    "Positional argument cannot follow keyword argument.\n  "
                    f"{anon.sql()}"
                )

            args.append(e)

    return f(*args, **kwargs)


def transform_anonymous(
    evaluator: MacroEvaluator,
    context: t.Dict[str, t.Any],
    anon: exp.Anonymous,
    handler: CustomFuncHandler,
):
    obj = send_anonymous_to_callable(anon, handler.to_obj)
    anon.replace(handler.transform(evaluator, context, obj))
