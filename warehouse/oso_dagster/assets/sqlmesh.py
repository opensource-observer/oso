import dagster as dg
from dagster import AssetExecutionContext, AssetSelection, RunConfig, define_asset_job
from dagster_sqlmesh import (
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
    SQLMeshResource,
    sqlmesh_assets,
)
from oso_dagster.factories.common import AssetFactoryResponse
from oso_dagster.resources.trino import TrinoResource
from oso_dagster.utils.asynctools import multiple_async_contexts

from ..factories import early_resources_asset_factory


class SQLMeshRunConfig(dg.Config):
    # Set this to True to restate the selected models
    restate_models: list[str] | None = None
    
    # Set this to True to dynamically identify models to restate based on entity_category tags
    restate_by_entity_category: bool = False
    # List of entity categories to restate (e.g., ["project", "collection"])
    restate_entity_categories: list[str] | None = None

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
    dev_environment = sqlmesh_infra_config["dev_environment"]
    environment = sqlmesh_infra_config["environment"]

    @sqlmesh_assets(
        config=sqlmesh_config,
        environment=environment,
        dagster_sqlmesh_translator=sqlmesh_translator,
        enabled_subsetting=False,
        op_tags=op_tags,
    )
    async def sqlmesh_project(
        context: AssetExecutionContext,
        sqlmesh: SQLMeshResource,
        trino: TrinoResource,
        config: SQLMeshRunConfig,
    ):

        restate_models = config.restate_models or []
        # Ensure that both trino and the mcs are available
        async with multiple_async_contexts(
            trino=trino.ensure_available(log_override=context.log),
        ):
            # If restate_by_entity_category is True, dynamically identify models based on entity categories
            if config.restate_by_entity_category:
                # Ensure we have entity categories to filter by
                if not config.restate_entity_categories:
                    context.log.info("restate_by_entity_category is True but no entity categories specified. Using both 'project' and 'collection'.")
                    entity_categories = ["project", "collection"]
                else:
                    entity_categories = config.restate_entity_categories
                    context.log.info(f"Filtering models by entity categories: {entity_categories}")

                for category in entity_categories:
                    restate_models.append(f"tag:entity_category={category}")
            
            # If we specify a dev_environment, we will first plan it for safety
            if dev_environment:
                context.log.info("Planning dev environment")
                all(
                    sqlmesh.run(
                        context,
                        environment=dev_environment,
                        plan_options={"skip_tests": True},
                        start=config.start,
                        end=config.end,
                        restate_models=config.restate_models,
                        skip_run=True,
                    )
                )

            context.log.info("Starting to process prod environment")
            for result in sqlmesh.run(
                context,
                environment=environment,
                plan_options={"skip_tests": True},
                start=config.start,
                end=config.end,
                restate_models=config.restate_models,
            ):
                yield result

    all_assets_selection = AssetSelection.assets(sqlmesh_project)
    
    return AssetFactoryResponse(
        assets=[sqlmesh_project],
        jobs=[
            define_asset_job(
                name="sqlmesh_all_assets",
                selection=all_assets_selection,
                description="All assets in the sqlmesh project",
            ),
            # Job to restate all project and collection related assets
            define_asset_job(
                name="sqlmesh_restate_project_collection_assets",
                selection=all_assets_selection,
                description="Restate all project and collection related assets",
                config=RunConfig(
                    ops={
                        "sqlmesh_project": SQLMeshRunConfig(
                            restate_by_entity_category=True,
                            restate_entity_categories=["project", "collection"],
                        ),
                    }
                ),
            ),
            # Job to restate only project related assets
            define_asset_job(
                name="sqlmesh_restate_project_assets",
                selection=all_assets_selection,
                description="Restate only project related assets",
                config=RunConfig(
                    ops={
                        "sqlmesh_project": SQLMeshRunConfig(
                            restate_by_entity_category=True,
                            restate_entity_categories=["project"],
                        ),
                    }
                ),
            ),
            # Job to restate only collection related assets
            define_asset_job(
                name="sqlmesh_restate_collection_assets",
                selection=all_assets_selection,
                description="Restate only collection related assets",
                config=RunConfig(
                    ops={
                        "sqlmesh_project": SQLMeshRunConfig(
                            restate_by_entity_category=True,
                            restate_entity_categories=["collection"],
                        )
                    }
                ),
            ),
        ],
    )
