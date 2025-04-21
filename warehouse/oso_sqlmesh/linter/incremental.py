import typing as t

from sqlglot import exp
from sqlmesh.core.linter.rule import Rule, RuleViolation
from sqlmesh.core.model import IncrementalByTimeRangeKind, Model


class IncrementalMustHaveTimePartition(Rule):
    """Incremental models must have a time partition."""

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        # Rule violated if the model's owner field (`model.owner`) is not specified
        if not isinstance(model.kind, IncrementalByTimeRangeKind):
            return None
        # Check if the model has a bucketed time partition
        time_column = model.time_column
        if time_column is None:
            return self.violation("Incremental by time range models must have a time column.")
        for ex in model.partitioned_by:
            for column in ex.find_all(exp.Column):
                if column.name == time_column.column.name:
                    return None
        return self.violation(
            f"Incremental by time range models must have a time partition on {time_column.column.name}."
        )
        
    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        # Create a RuleViolation object with the specified violation message
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or "Incremental models must have a time partition.",
        )