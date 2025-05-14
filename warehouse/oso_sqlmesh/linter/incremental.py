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

class IncrementalMustDefineNoGapsAudit(Rule):
    """Incremental models must have a time partition."""

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        # Rule violated if the model's owner field (`model.owner`) is not specified
        if not isinstance(model.kind, IncrementalByTimeRangeKind):
            return None
        
        for audit in model.audits:
            name, args = audit
            if name == "no_gaps":
                return None
        return self.violation(
            "Incremental by time range models must have a no_gaps audit."
        )

    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        # Create a RuleViolation object with the specified violation message
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or "Incremental models must have a time partition.",
        )

class IncrementalMustHaveLookback(Rule):
    """Incremental models must have a lookback defined that covers at least 1 month (31 days to be certain)."""

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        # Rule violated if the model's owner field (`model.owner`) is not specified
        if not isinstance(model.kind, IncrementalByTimeRangeKind):
            return None
        
        minimum_lookback_seconds = 31 * 24 * 60 * 60
        interval_unit = model.interval_unit
        interval_seconds = interval_unit.seconds

        minimum_lookback = minimum_lookback_seconds / interval_seconds

        if model.kind.lookback is None:
            return self.violation(f"Incremental by time range models must have a lookback defined of at least 31 days. At current settings this should be {minimum_lookback}")

        # Check if the lookback is at least 31 days (or 1 month)
        if interval_unit.is_month:
            if model.kind.lookback >= 1:
                return None
            return self.violation(
                f"Incremental by time range models must have a lookback of at least 31 days (or 1 month). Current lookback is {model.kind.lookback} {interval_unit.value}(s)."
            )

        lookback_seconds = model.kind.lookback * interval_seconds
        if lookback_seconds >= minimum_lookback_seconds:
            return None
        
        return self.violation(
            f"Incremental by time range models must have a lookback of at least 30 days. Current lookback is {model.kind.lookback} {interval_unit.value}(s)."
        )

    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        # Create a RuleViolation object with the specified violation message
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or "Incremental models must have a time partition.",
        )
    

class IncrementalMustHaveForwardOnly(Rule):
    """Incremental models must have forward_only set to True or specifically ignore this rule."""

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        # Rule violated if the model's owner field (`model.owner`) is not specified
        if not isinstance(model.kind, IncrementalByTimeRangeKind):
            return None
        
        if model.forward_only:
            return None
        return self.violation(
            "Incremental by time range models must have forward_only set to True or specifically ignore this rule."
        )
        
    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        # Create a RuleViolation object with the specified violation message
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or "Incremental models must have a time partition.",
        )