import typing as t

from metrics_tools.intermediate import run_intermediate_macro_evaluator
from metrics_tools.models.tools import create_unregistered_wrapped_macro
from sqlglot import exp
from sqlmesh.core.macros import MacroRegistry

from .base import Transform


class IntermediateMacroEvaluatorTransform(Transform):
    def __init__(
        self,
        macros: t.List[t.Callable | t.Tuple[t.Callable, t.List[str]]],
        variables: t.Dict[str, t.Any],
    ):
        self._macros = macros
        self._variables = variables

    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        registry = MacroRegistry("intermediate_macros")
        for macro in self._macros:
            if isinstance(macro, tuple):
                func, aliases = macro
                registry.update(create_unregistered_wrapped_macro(func, aliases))
            else:
                registry.update(create_unregistered_wrapped_macro(macro))

        final = []
        for expression in query:
            evaluated = run_intermediate_macro_evaluator(
                expression, macros=registry, variables=self._variables
            )
            assert evaluated is not None
            final.extend(evaluated)
        return final
