from dagster import AssetExecutionContext, AssetKey
from dagster_sqlmesh import (
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
    SQLMeshResource,
    sqlmesh_assets,
)
from oso_dagster.resources.mcs import MCSResource
from oso_dagster.resources.trino import TrinoResource
from oso_dagster.utils.asynctools import multiple_async_contexts
from sqlmesh import Context
from sqlmesh.core.model import Model

from ..factories import early_resources_asset_factory


class PrefixedSQLMeshTranslator(SQLMeshDagsterTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key_fqn(self, context: Context, fqn: str) -> AssetKey:
        key = super().get_asset_key_fqn(context, fqn)
        return key.with_prefix("production").with_prefix("dbt")

    def get_asset_key_from_model(self, context: Context, model: Model) -> AssetKey:
        key = super().get_asset_key_from_model(context, model)
        return key.with_prefix(self._prefix)


@early_resources_asset_factory()
def sqlmesh_factory(sqlmesh_infra_config: dict, sqlmesh_config: SQLMeshContextConfig):
    environment = sqlmesh_infra_config["environment"]

    @sqlmesh_assets(
        config=sqlmesh_config,
        environment=environment,
        dagster_sqlmesh_translator=PrefixedSQLMeshTranslator("metrics"),
    )
    async def sqlmesh_project(
        context: AssetExecutionContext,
        sqlmesh: SQLMeshResource,
        trino: TrinoResource,
        mcs: MCSResource,
    ):
        # Ensure that both trino and the mcs are available
        async with multiple_async_contexts(
            trino=trino.ensure_available(log_override=context.log),
            mcs=mcs.ensure_available(),
        ):
            for result in sqlmesh.run(
                context, environment=environment, plan_options={"skip_tests": True}
            ):
                yield result

    return sqlmesh_project
