
from dagster import AssetKey, AssetExecutionContext
from dagster_sqlmesh import (
    SQLMeshDagsterTranslator,
    sqlmesh_assets,
    SQLMeshContextConfig,
    SQLMeshResource,
)
from sqlmesh import Context
from sqlmesh.core.model import Model
from ..factories import early_resources_asset_factory


class PrefixedSQLMeshTranslator(SQLMeshDagsterTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key_fqn(self, context: Context, fqn: str) -> AssetKey:
        key = super().get_asset_key_fqn(context, fqn)
        return key.with_prefix("clickhouse")

    def get_asset_key_from_model(self, context: Context, model: Model) -> AssetKey:
        key = super().get_asset_key_from_model(context, model)
        return key.with_prefix(self._prefix)


@early_resources_asset_factory()
def sqlmesh_factory(sqlmesh_config: SQLMeshContextConfig):
    @sqlmesh_assets(
        config=sqlmesh_config,
        dagster_sqlmesh_translator=PrefixedSQLMeshTranslator("metrics"),
    )
    def sqlmesh_project(context: AssetExecutionContext, sqlmesh: SQLMeshResource):
        yield from sqlmesh.run(context, environment="prod")

    return sqlmesh_project
