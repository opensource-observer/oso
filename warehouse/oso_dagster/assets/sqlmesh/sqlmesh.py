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
from oso_core.cache.types import CacheMetadataOptions
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import AssetFactoryResponse, cacheable_asset_factory
from oso_dagster.factories.common import CacheableDagsterContext
from oso_dagster.resources.heartbeat import HeartBeatResource
from oso_dagster.resources.trino import TrinoResource
from oso_dagster.utils.asynctools import multiple_async_contexts
from pydantic import BaseModel


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

    use_dev_environment: bool = False


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
    },
    "dagster/concurrency_key": "sqlmesh",
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
    # If we're in a deployed environment at build time, we can
    # cache the sqlmesh build indefinitely
    @cache_context.register_generator(
        cacheable_type=CacheableSQLMeshMultiAssetOptions,
        extra_cache_key_metadata=dict(
            sqlmesh_gateway=global_config.sqlmesh_gateway,
        ),
        cache_metadata_options=CacheMetadataOptions.with_no_expiration_if(
            global_config.run_mode == "build" and global_config.in_deployed_container
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

    @cache_context.register_hydrator()
    def sqlmesh_assets_hydrator(
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
            heartbeat: HeartBeatResource,
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

                # If we specify a dev_environment, we will first plan it for
                # safety. Restatements are ignored as they may end up duplicating
                # work based on how restatement in planning works.
                if (
                    dev_environment
                    and config.use_dev_environment
                    and not config.restate_models
                ):
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
                            materializations_enabled=False,
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
                # Start a heartbeat to indicate that sqlmesh is running
                async with heartbeat.heartbeat(
                    job_name="sqlmesh", interval_seconds=300, log_override=context.log
                ):
                    async with multiple_async_contexts(
                        trino=trino.ensure_available(log_override=context.log),
                    ):
                        for result in run_sqlmesh(context, sqlmesh, config):
                            yield result
            else:
                # If we are not running trino we are using duckdb
                for result in run_sqlmesh(context, sqlmesh, config):
                    yield result

        # Define a job that checks the heartbeat of sqlmesh runs. If the
        # heartbeat is older than 30 minutes, we scale trino down to zero.
        @dg.op
        async def sqlmesh_heartbeat_checker(
            context: dg.OpExecutionContext,
            global_config: ResourceParam[DagsterConfig],
            trino: TrinoResource,
            heartbeat: HeartBeatResource,
        ) -> None:
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc)

            last_heartbeat = await heartbeat.get_last_heartbeat_for("sqlmesh")
            if last_heartbeat is None:
                context.log.info(
                    "No heartbeat found for sqlmesh now ensuring trino shutdown."
                )
                last_heartbeat = now - timedelta(
                    minutes=global_config.sqlmesh_trino_ttl_minutes + 1
                )

            # Only scale down trino if we're in a k8s environment
            if not global_config.k8s_enabled:
                return

            if now - last_heartbeat > timedelta(
                minutes=global_config.sqlmesh_trino_ttl_minutes
            ):
                context.log.info(
                    f"No heartbeat detected for sqlmesh in the last {global_config.sqlmesh_trino_ttl_minutes} minutes. Ensuring that producer trino is scaled down."
                )
                await trino.ensure_shutdown()
            else:
                context.log.info("Heartbeat detected for sqlmesh. No action needed.")

        # Use the in-process executor for the heartbeat monitor job to avoid
        # the overhead of spinning up a new k8s pod in addition to the run launcher
        @dg.job(executor_def=dg.in_process_executor)
        def sqlmesh_heartbeat_monitor_job():
            sqlmesh_heartbeat_checker()

        all_assets_selection = AssetSelection.assets(sqlmesh_project)

        return AssetFactoryResponse(
            assets=[sqlmesh_project],
            jobs=[
                sqlmesh_heartbeat_monitor_job,
                define_asset_job(
                    name="sqlmesh_all_assets",
                    selection=all_assets_selection,
                    description="All assets in the sqlmesh project",
                ),
                define_asset_job(
                    name="sqlmesh_all_assets_with_dev_environment",
                    selection=all_assets_selection,
                    description="All assets in the sqlmesh project with dev environment",
                    config=RunConfig(
                        ops={
                            "sqlmesh_project": SQLMeshRunConfig(
                                use_dev_environment=True,
                            ),
                        }
                    ),
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
            schedules=[
                dg.ScheduleDefinition(
                    name="sqlmesh_heartbeat_monitor_schedule",
                    job=sqlmesh_heartbeat_monitor_job,
                    cron_schedule="*/15 * * * *",
                )
            ],
        )

    return cache_context
