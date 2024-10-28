import typing as t

from metrics_tools.intermediate import intermediate_macro_evaluator
from metrics_tools.models import create_unregistered_wrapped_macro
from sqlmesh.core.macros import MacroRegistry
from sqlglot import exp

from .base import Transform


class IntermediateMacroEvaluatorTransform(Transform):
    def __init__(self, macros: t.List[t.Callable], variables: t.Dict[str, t.Any]):
        self._macros = macros
        self._variables = variables

    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        for macro in self._macros:
            registry = create_unregistered_wrapped_macro(macro)
        else:
            registry = t.cast(MacroRegistry, {})

        final = []
        for expression in query:
            final.append(
                intermediate_macro_evaluator(
                    expression, macros=registry, variables=self._variables
                )
            )
        return final
