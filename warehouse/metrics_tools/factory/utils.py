import typing as t
from contextlib import contextmanager

from metrics_tools.definition import PeerMetricDependencyRef
from sqlmesh.core.macros import MacroEvaluator


@contextmanager
def metric_ref_evaluator_context(
    evaluator: MacroEvaluator,
    ref: PeerMetricDependencyRef,
    additional_vars: t.Optional[t.Dict[str, t.Any]] = None,
    additional_macros: t.Optional[t.Dict[str, t.Any]] = None,
):
    before_locals = evaluator.locals.copy()
    before_macros = evaluator.macros.copy()

    evaluator.locals.update(additional_vars or {})
    evaluator.locals.update(
        {
            "rolling_window": ref.get("window"),
            "rolling_unit": ref.get("unit"),
            "time_aggregation": ref.get("time_aggregation"),
            "entity_type": ref.get("entity_type"),
        }
    )
    evaluator.macros.update(additional_macros or {})
    try:
        yield
    finally:
        evaluator.locals = before_locals
        evaluator.macros = before_macros
