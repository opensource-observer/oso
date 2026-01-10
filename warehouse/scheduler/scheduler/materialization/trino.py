from scheduler.types import (
    MaterializationStrategy,
    TableReference,
)


class TrinoMaterializationStrategy(MaterializationStrategy):
    def __init__(self, base_catalog_name: str):
        self._base_catalog_name = base_catalog_name

    def destination_fqn(self, ref: TableReference) -> str:
        # Remove all hyphens from org_id and dataset_id
        org_id = ref.org_id.replace("-", "")
        dataset_id = ref.dataset_id.replace("-", "")

        return f"{self._base_catalog_name}.org_{org_id}__{dataset_id}.{ref.table_id}"
