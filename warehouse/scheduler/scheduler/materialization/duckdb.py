from scheduler.types import (
    MaterializationStrategy,
    TableReference,
)


class DuckdbMaterializationStrategy(MaterializationStrategy):
    def __init__(self, base_catalog_name: str):
        self._base_catalog_name = base_catalog_name

    def destination_fqn(self, ref: TableReference) -> str:
        """Get the fully qualified destination name for the given table reference."""
        return f"{self._base_catalog_name}.org_{ref.org_id}__{ref.dataset_id}.{ref.table_id}"
