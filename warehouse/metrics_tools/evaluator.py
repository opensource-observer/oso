# import typing as t

# from .dialect.translate import (
#     CustomFuncRegistry,
#     send_anonymous_to_callable,
# )
# from sqlmesh.core.macros import MacroEvaluator
# from sqlglot import exp


# class FunctionsTransformer:
#     def __init__(
#         self,
#         registry: CustomFuncRegistry,
#         evaluator: MacroEvaluator,
#         context: t.Dict[str, t.Any],
#     ):
#         self._registry = registry
#         self._evaluator = evaluator
#         self._context = context

#     def transform(self, expression: exp.Expression):
#         expression = expression.copy()
#         for anon in expression.find_all(exp.Anonymous):
#             handler = self._registry.get(anon.this)
#             if handler:
#                 obj = send_anonymous_to_callable(anon, handler.to_obj)
#                 anon.replace(handler.transform(self._evaluator, self._context, obj))
#         return expression
