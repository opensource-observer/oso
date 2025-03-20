import dagster as dg
from dagster import AssetExecutionContext, AssetSelection, define_asset_job
from dagster_sqlmesh import (
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
    SQLMeshResource,
    sqlmesh_assets,
)
from oso_dagster.factories.common import AssetFactoryResponse
from oso_dagster.resources.mcs import MCSResource
from oso_dagster.resources.trino import TrinoResource
from oso_dagster.utils.asynctools import multiple_async_contexts

from ..factories import early_resources_asset_factory


class SQLMeshRunConfig(dg.Config):
    # Set this to True to restate the selected models
    restate_selected: bool = False

    start: str | None = None
    end: str | None = None


op_tags = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "2500m", "memory": "5120Mi"},
                "limits": {"memory": "10240Mi"},
            },
        },
        "pod_spec_config": {
            "node_selector": {"pool_type": "standard"},
            "tolerations": [
                {
                    "key": "pool_type",
                    "operator": "Equal",
                    "value": "standard",
                    "effect": "NoSchedule",
                }
            ],
        },
        "merge_behavior": "SHALLOW",
    }
}


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
        enabled_subsetting=True,
        op_tags=op_tags,
    )
    async def sqlmesh_project(
        context: AssetExecutionContext,
        sqlmesh: SQLMeshResource,
        trino: TrinoResource,
        mcs: MCSResource,
        config: SQLMeshRunConfig,
    ):
        # Ensure that both trino and the mcs are available
        async with multiple_async_contexts(
            trino=trino.ensure_available(log_override=context.log),
            mcs=mcs.ensure_available(log_override=context.log),
        ):
            for result in sqlmesh.run(
                context,
                environment=environment,
                plan_options={"skip_tests": True},
                start=config.start,
                end=config.end,
                restate_selected=config.restate_selected,
            ):
                yield result

    all_assets_selection = AssetSelection.assets(sqlmesh_project)
    metrics_assets_selection = all_assets_selection.tag(
        key="model_category", value="metrics"
    )

    return AssetFactoryResponse(
        assets=[sqlmesh_project],
        jobs=[
            define_asset_job(
                name="sqlmesh_all_assets",
                selection=all_assets_selection,
                description="All assets in the sqlmesh project",
            ),
            define_asset_job(
                name="sqlmesh_no_metrics_assets",
                selection=all_assets_selection - metrics_assets_selection,
                description="All assets in the sqlmesh project except metrics",
            ),
            define_asset_job(
                name="sqlmesh_metrics_assets",
                selection=metrics_assets_selection,
                description="Only metrics assets in the  sqlmesh project",
            ),
        ],
    )
