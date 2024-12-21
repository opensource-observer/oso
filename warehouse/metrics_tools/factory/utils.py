import typing as t
from contextlib import contextmanager

from metrics_tools.definition import PeerMetricDependencyRef
from sqlmesh.core.macros import MacroEvaluator


@contextmanager
def metric_ref_evaluator_context(
    evaluator: MacroEvaluator,
    ref: PeerMetricDependencyRef,
    extra_vars: t.Optional[t.Dict[str, t.Any]] = None,
):
    before = evaluator.locals.copy()
    evaluator.locals.update(extra_vars or {})
    evaluator.locals.update(
        {
            "rolling_window": ref.get("window"),
            "rolling_unit": ref.get("unit"),
            "time_aggregation": ref.get("time_aggregation"),
            "entity_type": ref.get("entity_type"),
        }
    )
    try:
        yield
    finally:
        evaluator.locals = before
