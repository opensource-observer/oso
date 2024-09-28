"""
Create a sqlmesh render that doesn't need to use the rest of sqlmesh.
"""

import typing as t
from dataclasses import dataclass
from pathlib import Path

from sqlglot import exp
from sqlglot.helper import ensure_list
from sqlmesh.core.macros import MacroEvaluator, RuntimeStage
from sqlmesh.core.model import SqlModel, model


@dataclass(kw_only=True)
class FakeEngineAdapter:
    dialect: str


def render(
    dialect: str,
    model_name: str,
    additional_locals: t.Optional[t.Dict[str, t.Any]] = None,
):
    model_inst = model.get_registry()[model_name].model(
        module_path=Path("."), path=Path(".")
    )
    if not isinstance(model_inst, SqlModel):
        raise Exception("Not a sql model")
    query_renderer = model_inst._query_renderer
    expressions = ensure_list(query_renderer._expression)
    evaluator = MacroEvaluator(
        dialect,
        python_env=query_renderer._python_env,
        runtime_stage=RuntimeStage.EVALUATING,
    )

    evaluator.locals["engine_adapter"] = FakeEngineAdapter(dialect="clickhouse")
    evaluator.locals.update(additional_locals or {})

    transformed_expressions: t.List[exp.Expression | t.List[exp.Expression] | None] = []

    for definitions in query_renderer._macro_definitions:
        evaluator.evaluate(definitions)

    for expression in expressions:
        transformed_expressions.append(evaluator.transform(expression))

    return transformed_expressions
