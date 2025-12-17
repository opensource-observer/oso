import typing as t
from contextlib import asynccontextmanager

from scheduler.types import (
    MaterializationStrategy,
    MaterializationStrategyResource,
    TableReference,
)
from sqlglot import exp
from sqlmesh import EngineAdapter
from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter


class DuckdbMaterializationStrategyResource(MaterializationStrategyResource):
    @asynccontextmanager
    async def get_strategy(
        self, adapter: EngineAdapter
    ) -> t.AsyncIterator[MaterializationStrategy]:
        assert isinstance(adapter, DuckDBEngineAdapter), (
            "Adapter must be a DuckDBEngineAdapter"
        )
        yield DuckdbMaterializationStrategy(adapter=adapter)


class DuckdbMaterializationStrategy(MaterializationStrategy):
    def __init__(self, adapter: DuckDBEngineAdapter):
        self._adapter = adapter

    @property
    def engine_adapter(self) -> EngineAdapter:
        return self._adapter

    async def fqn_to_table_reference(self, fqn) -> TableReference:
        """Duckdb materialization is in the form
        catalog.org_{org_id}__ds_{dataset_id}.tbl_{table_id}
        """
        table = exp.to_table(fqn)
        # Catalog is ignored for DuckDB
        db = table.db
        table_name = table.name

        split_db = db.split("__")

        if not len(split_db) == 2:
            raise ValueError(f"Invalid DuckDB table FQN: {fqn}")

        org_id = split_db[0].replace("org_", "")
        dataset_id = split_db[1].replace("ds_", "")
        table_id = table_name.replace("tbl_", "")

        return TableReference(
            org_id=org_id,
            dataset_id=dataset_id,
            table_id=table_id,
        )

    async def table_reference_to_fqn(self, ref: TableReference) -> str:
        catalog = self._adapter.get_current_catalog()
        return f"{catalog}.org_{ref.org_id}__ds_{ref.dataset_id}.tbl_{ref.table_id}"
