import typing as t
from contextlib import asynccontextmanager

from scheduler.types import (
    MaterializationStrategy,
    MaterializationStrategyResource,
    TableReference,
)
from sqlglot import exp
from sqlmesh import EngineAdapter
from sqlmesh.core.engine_adapter.trino import TrinoEngineAdapter


class TrinoMaterializationStrategyResource(MaterializationStrategyResource):
    def __init__(self, iceberg_catalog_name: str):
        self.iceberg_catalog_name = iceberg_catalog_name

    @asynccontextmanager
    async def get_strategy(
        self, adapter: EngineAdapter
    ) -> t.AsyncIterator[MaterializationStrategy]:
        assert isinstance(adapter, TrinoEngineAdapter), (
            "Adapter must be a TrinoEngineAdapter"
        )
        yield TrinoMaterializationStrategy(
            iceberg_catalog_name=self.iceberg_catalog_name, adapter=adapter
        )


class TrinoMaterializationStrategy(MaterializationStrategy):
    def __init__(self, iceberg_catalog_name: str, adapter: TrinoEngineAdapter):
        self._adapter = adapter
        self._iceberg_catalog_name = iceberg_catalog_name

    @property
    def engine_adapter(self) -> EngineAdapter:
        return self._adapter

    async def fqn_to_table_reference(self, fqn) -> TableReference:
        """Iceberg materialization is in the form
        {iceberg_catalog_name}.org_{org_id}__ds_{dataset_id}.tbl_{table_id}
        """
        table = exp.to_table(fqn)
        # Catalog is ignored for Trino as we set it to iceberg_catalog_name
        db = table.db
        table_name = table.name

        split_db = db.split("__")

        if not len(split_db) == 2:
            raise ValueError(f"Invalid Trino table FQN: {fqn}")

        org_id = split_db[0].replace("org_", "")
        dataset_id = split_db[1].replace("ds_", "")
        table_id = table_name.replace("tbl_", "")

        return TableReference(
            org_id=org_id,
            dataset_id=dataset_id,
            table_id=table_id,
        )

    async def table_reference_to_fqn(self, ref: TableReference) -> str:
        return f"{self._iceberg_catalog_name}.org_{ref.org_id}__ds_{ref.dataset_id}.tbl_{ref.table_id}"
