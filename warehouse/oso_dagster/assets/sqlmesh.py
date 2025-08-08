import copy
import typing as t

import dagster as dg
from dagster import (
    AssetExecutionContext,
    AssetSelection,
    ResourceParam,
    RunConfig,
    define_asset_job,
)
from dagster_sqlmesh import (
    IntermediateAssetDep,
    IntermediateAssetOut,
    PlanOptions,
    SQLMeshContextConfig,
    SQLMeshDagsterTranslator,
    SQLMeshMultiAssetOptions,
    SQLMeshResource,
    sqlmesh_asset_from_multi_asset_options,
    sqlmesh_to_multi_asset_options,
)
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import CacheableDagsterContext
from oso_dagster.resources.trino import TrinoResource
from oso_dagster.utils.asynctools import multiple_async_contexts
from pydantic import BaseModel

from ..factories import AssetFactoryResponse, cacheable_asset_factory


class SQLMeshRunConfig(dg.Config):
    # Set this to True to restate the selected models
    restate_models: list[str] | None = None

    # Set this to True to dynamically identify models to restate based on entity_category tags
    restate_by_entity_category: bool = False
    # List of entity categories to restate (e.g., ["project", "collection"])
    restate_entity_categories: list[str] | None = None

    allow_destructive_models: list[str] | None = None

    skip_tests: bool = False

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


class CacheableSQLMeshMultiAssetOptions(BaseModel):
    """A cacheable version of SQLMeshMultiAssetOptions that can be used to create
    a dagster multi_asset definition. This is primarily used to enable caching
    of SQLMesh assets in Dagster."""

    outs: t.Mapping[str, IntermediateAssetOut]
    deps: list[IntermediateAssetDep]
    internal_asset_deps: t.Mapping[str, set[str]]

    @classmethod
    def from_sqlmesh_multi_asset_options(
        cls, sqlmesh_multi_asset_options: SQLMeshMultiAssetOptions
    ) -> "CacheableSQLMeshMultiAssetOptions":
        """Convert a SQLMeshMultiAssetOptions to a CacheableSQLMeshMultiAssetOptions."""

        outs: t.Dict[str, IntermediateAssetOut] = {}
        for key, out in sqlmesh_multi_asset_options.outs.items():
            assert isinstance(out, IntermediateAssetOut)
            outs[key] = out

        deps: t.List[IntermediateAssetDep] = []
        for dep in sqlmesh_multi_asset_options.deps:
            assert isinstance(dep, IntermediateAssetDep)
            deps.append(dep)

        return cls(
            outs=outs,
            deps=deps,
            internal_asset_deps=copy.deepcopy(
                sqlmesh_multi_asset_options.internal_asset_deps
            ),
        )

    def to_sqlmesh_multi_asset_options(self) -> SQLMeshMultiAssetOptions:
        return SQLMeshMultiAssetOptions(
            outs=self.outs,
            deps=list(self.deps)[:],
            internal_asset_deps=copy.deepcopy(self.internal_asset_deps),
        )


@cacheable_asset_factory(tags=dict(run_at_build="true"))
def sqlmesh_factory(
    global_config: DagsterConfig, cache_context: CacheableDagsterContext
):
    @cache_context.register_generator(
        cacheable_type=CacheableSQLMeshMultiAssetOptions,
        extra_cache_key_metadata=dict(
            sqlmesh_gateway=global_config.sqlmesh_gateway,
        ),
    )
    def cacheable_sqlmesh_multi_asset_options(
        *,
        sqlmesh_infra_config: dict,
        sqlmesh_context_config: SQLMeshContextConfig,
        sqlmesh_translator: SQLMeshDagsterTranslator,
    ) -> CacheableSQLMeshMultiAssetOptions:
        environment = sqlmesh_infra_config["environment"]

        return CacheableSQLMeshMultiAssetOptions.from_sqlmesh_multi_asset_options(
            sqlmesh_to_multi_asset_options(
                config=sqlmesh_context_config,
                environment=environment,
                dagster_sqlmesh_translator=sqlmesh_translator,
            )
        )

    @cache_context.register_rehydrator()
    def sqlmesh_assets_rehydrator(
        cacheable_sqlmesh_multi_asset_options: CacheableSQLMeshMultiAssetOptions,
        sqlmesh_infra_config: dict,
    ):
        dev_environment = sqlmesh_infra_config["dev_environment"]
        environment = sqlmesh_infra_config["environment"]

        @sqlmesh_asset_from_multi_asset_options(
            sqlmesh_multi_asset_options=cacheable_sqlmesh_multi_asset_options.to_sqlmesh_multi_asset_options(),
            enabled_subsetting=False,
            op_tags=op_tags,
        )
        async def sqlmesh_project(
            context: AssetExecutionContext,
            global_config: ResourceParam[DagsterConfig],
            sqlmesh: SQLMeshResource,
            trino: TrinoResource,
            config: SQLMeshRunConfig,
        ):
            restate_models = config.restate_models[:] if config.restate_models else []

            # We use this helper function so we can run sqlmesh both locally and in
            # a k8s environment
            def run_sqlmesh(
                context: AssetExecutionContext,
                sqlmesh: SQLMeshResource,
                config: SQLMeshRunConfig,
            ):
                # If restate_by_entity_category is True, dynamically identify models based on entity categories
                if config.restate_by_entity_category:
                    # Ensure we have entity categories to filter by
                    if not config.restate_entity_categories:
                        context.log.info(
                            "restate_by_entity_category is True but no entity categories specified. Using both 'project' and 'collection'."
                        )
                        entity_categories = ["project", "collection"]
                    else:
                        entity_categories = config.restate_entity_categories
                        context.log.info(
                            f"Filtering models by entity categories: {entity_categories}"
                        )

                    for category in entity_categories:
                        restate_models.append(f"tag:entity_category={category}")

                plan_options: PlanOptions = {"skip_tests": config.skip_tests}
                if config.allow_destructive_models:
                    plan_options["allow_destructive_models"] = (
                        config.allow_destructive_models
                    )

                # If we specify a dev_environment, we will first plan it for safety
                if dev_environment:
                    context.log.info("Planning dev environment")
                    all(
                        sqlmesh.run(
                            context,
                            environment=dev_environment,
                            plan_options=copy.deepcopy(plan_options),
                            start=config.start,
                            end=config.end,
                            restate_models=restate_models,
                            skip_run=True,
                        )
                    )

                context.log.info("Starting to process prod environment")
                for result in sqlmesh.run(
                    context,
                    environment=environment,
                    plan_options=copy.deepcopy(plan_options),
                    start=config.start,
                    end=config.end,
                    restate_models=restate_models,
                ):
                    yield result

            # Trino can either be `local-trino` or `trino`
            if "trino" in global_config.sqlmesh_gateway:
                async with multiple_async_contexts(
                    trino=trino.ensure_available(log_override=context.log),
                ):
                    for result in run_sqlmesh(context, sqlmesh, config):
                        yield result
            else:
                # If we are not running trino we are using duckdb
                for result in run_sqlmesh(context, sqlmesh, config):
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

    return cache_context
