"""
Auxiliary resources for sqlmesh
"""

import typing as t
from datetime import datetime

from dagster import AssetKey, AssetsDefinition, asset
from dagster_sqlmesh import SQLMeshDagsterTranslator
from dagster_sqlmesh.controller.base import SQLMeshInstance
from sqlmesh import Context
from sqlmesh.core.model import Model


class SQLMeshExporter:
    name: str

    def create_export_asset(
        self, mesh: SQLMeshInstance, name: str, model: Model, key: AssetKey
    ) -> AssetsDefinition:
        raise NotImplementedError("Not implemented")


class PrefixedSQLMeshTranslator(SQLMeshDagsterTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key_fqn(self, context: Context, fqn: str) -> AssetKey:
        key = super().get_asset_key_fqn(context, fqn)
        return key.with_prefix("production").with_prefix("dbt")

    def get_asset_key_from_model(self, context: Context, model: Model) -> AssetKey:
        key = super().get_asset_key_from_model(context, model)
        return key.with_prefix(self._prefix)


class Trino2ClickhouseSQLMeshExporter(SQLMeshExporter):
    def __init__(
        self,
        prefix: str | t.List[str],
        *,
        destination_catalog: str,
        destination_schema: str,
        source_catalog: str,
        source_schema: str,
    ):
        self._prefix = prefix

        self._destination_catalog = destination_catalog
        self._destination_schema = destination_schema

        self._source_catalog = source_catalog
        self._source_schema = source_schema

    def trino_destination_table(self, table_name: str):
        return f"{self._destination_catalog}.{self._destination_schema}.{table_name}"

    def clickhouse_destination_table(self, table_name: str):
        return f"{self._destination_schema}.{table_name}"

    def trino_source_table(self, table_name: str):
        return f"{self._source_catalog}.{self._source_schema}.{table_name}"

    def convert_model_key_to_clickhouse_key(self, key: AssetKey) -> AssetKey:
        return AssetKey(key.path[-1]).with_prefix(self._prefix)

    def create_export_asset(
        self, mesh: SQLMeshInstance, name: str, model: Model, key: AssetKey
    ) -> AssetsDefinition:
        from .clickhouse import ClickhouseResource
        from .trino import TrinoResource

        clickhouse_key = self.convert_model_key_to_clickhouse_key(key)

        @asset(
            key=clickhouse_key,
            deps=[key],
            compute_kind="sqlmesh-export",
        )
        def export(trino: TrinoResource, clickhouse: ClickhouseResource) -> None:
            table_name = key.path[-1]
            with trino.get_client() as trino_client:
                # Export the data from trino to clickhouse by creating a table
                # that has a suffix
                exported_table_name = f"{clickhouse_key.path[-1]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                trino_client.query(
                    f"""
                    CREATE TABLE {self.trino_destination_table(exported_table_name)}
                    WITH (
                        engine = "MergeTree"
                    )
                    AS 
                    SELECT * FROM {self.trino_source_table(key.path[-1])}
                """
                )

            with clickhouse.get_client() as clickhouse_client:
                # Create the clickhouse table
                clickhouse_client.query(
                    f"""
                    CREATE OR REPLACE VIEW IF NOT EXISTS {self._destination_schema}.{table_name} AS
                    SELECT * FROM {self.clickhouse_destination_table(exported_table_name)}
                """
                )
            return None

        return export
