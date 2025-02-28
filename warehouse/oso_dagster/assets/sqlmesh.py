from dagster import AssetExecutionContext
from dagster_sqlmesh import (
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
    SQLMeshResource,
    sqlmesh_assets,
)
from oso_dagster.resources.mcs import MCSResource
from oso_dagster.resources.trino import TrinoResource
from oso_dagster.utils.asynctools import multiple_async_contexts

from ..factories import early_resources_asset_factory


@early_resources_asset_factory()
def sqlmesh_factory(
    sqlmesh_infra_config: dict,
    sqlmesh_config: SQLMeshContextConfig,
    sqlmesh_translator: SQLMeshDagsterTranslator,
):
    environment = sqlmesh_infra_config["environment"]

    @sqlmesh_assets(
        config=sqlmesh_config,
        environment=environment,
        dagster_sqlmesh_translator=sqlmesh_translator,
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
            mcs=mcs.ensure_available(log_override=context.log),
        ):
            for result in sqlmesh.run(
                context, environment=environment, plan_options={"skip_tests": True}
            ):
                yield result

    return sqlmesh_project
