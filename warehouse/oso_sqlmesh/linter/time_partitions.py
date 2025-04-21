import typing as t

from sqlglot import exp
from sqlmesh.core.linter.rule import Rule, RuleViolation
from sqlmesh.core.model import Model


class TimePartitionsMustBeBucketed(Rule):
    """If a time partition is specified, it must be bucketed."""

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        # Rule violated if the model's owner field (`model.owner`) is not specified
        columns_to_types = model.columns_to_types

        if not columns_to_types:
            return None

        time_columns: list[str] = []

        for name, data_type in columns_to_types.items():
            dt = data_type.this
            assert isinstance(dt, exp.DataType.Type)
            if dt.value in [
                "DATE",
                "DATE32",
                "TIMESTAMP",
                "TIMESTAMP_NS",
                "TIMESTAMP_MS",
                "TIMESTAMP_S",
                "TIMESTAMPLTZ",
                "TIMESTAMPNTZ",
                "TIMESTAMPTZ",
                "TIMETZ",
                "DATETIME",
                "DATETIME64",
                "DATETIME2",
            ]:
                time_columns.append(name)

        for partition_exp in model.partitioned_by:
            if isinstance(partition_exp, exp.Column):
                if partition_exp.name in time_columns:
                    return self.violation(
                        f"Time partition {partition_exp.name} must use a time bucket for partitioning."
                    )

        return None

    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        # Create a RuleViolation object with the specified violation message
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg
            or "Incremental models must have a time partition.",
        )
