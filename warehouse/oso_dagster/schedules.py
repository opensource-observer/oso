from datetime import datetime, timezone
from typing import Generator, Iterable, List, cast

import dagster as dg
from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    DefaultScheduleStatus,
    RunRequest,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    define_asset_job,
)
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import AssetFactoryResponse, FactoryJobDefinition
from oso_dagster.utils.tags import (
    experimental_tag,
    partitioned_assets,
    sbom_source_tag,
    sqlmesh_source_downstream_tag,
    sqlmesh_source_tag,
    stable_source_tag,
    unstable_source_tag,
)


def get_partitioned_schedules(
    factory: AssetFactoryResponse,
) -> List[ScheduleDefinition]:
    resolved_assets = partitioned_assets.resolve(
        cast(Iterable[AssetsDefinition], factory.assets)
    )

    def create_schedule(asset_key: AssetKey):
        asset_path = "_".join(asset_key.path)
        job_name = f"{asset_path}_job"
        factory_job = factory.find_job_by_name(job_name)

        if not factory_job:
            raise ValueError(f"Job {job_name} not found in factory response")

        def execution_fn(
            context: ScheduleEvaluationContext,
        ) -> Generator[RunRequest, None, None]:
            if not factory_job.partitions_def:
                raise ValueError(
                    f"Job {job_name} does not have a partitions definition, but is being used "
                    "in a partitioned schedule"
                )

            materialized_partitions = set(
                context.instance.get_materialized_partitions(asset_key)
            )

            yield from (
                RunRequest(
                    run_key=f"{asset_path}_{partition_key}",
                    partition_key=partition_key,
                    tags={
                        "dagster/priority": "-1",
                    },
                )
                for partition_key in factory_job.partitions_def.get_partition_keys()
                if partition_key not in materialized_partitions
            )

        # Run unmaterilized partitions every sunday at midnight
        return ScheduleDefinition(
            job=factory_job,
            cron_schedule="0 0 * * 0",
            name=f"materialize_{asset_path}_schedule",
            execution_fn=execution_fn,
            default_status=DefaultScheduleStatus.STOPPED,
        )

    return [create_schedule(asset_key) for asset_key in resolved_assets]


def is_first_or_fifteenth_of_the_month() -> bool:
    today = datetime.now(timezone.utc)
    if today.day in [1, 15]:
        return True
    return False


def default_schedules(global_config: DagsterConfig) -> AssetFactoryResponse:
    """Used to define the default schedules for the default code location. We
    wrap this is a factory function because if sqlmesh is disabled, this will
    fail to run correctly locally."""

    core_assets = (
        AssetSelection.all()
        - experimental_tag
        - stable_source_tag
        - unstable_source_tag
        - sbom_source_tag
        - partitioned_assets
    )

    if global_config.sqlmesh_assets_on_default_code_location_enabled:
        core_assets = core_assets - sqlmesh_source_downstream_tag

    materialize_core_assets = define_asset_job(
        "materialize_core_assets_job",
        core_assets,
    )

    materialize_sqlmesh_assets = define_asset_job(
        "materialize_sqlmesh_assets_job",
        sqlmesh_source_tag,
    )

    materialize_stable_source_assets = define_asset_job(
        "materialize_stable_source_assets_job",
        stable_source_tag,
    )

    materialize_unstable_source_assets = define_asset_job(
        "materialize_unstable_source_assets_job",
        unstable_source_tag,
    )

    materialize_sbom_source_assets = define_asset_job(
        "materialize_sbom_assets_job",
        sbom_source_tag,
    )

    schedules: list[ScheduleDefinition] = [
        # Run core pipeline assets once a month at 00:00 UTC
        ScheduleDefinition(
            job=materialize_core_assets,
            cron_schedule="0 0 1 * *",
            tags={
                "dagster/priority": "-1",
            },
        ),
        # Run source assets every day
        ScheduleDefinition(
            job=materialize_stable_source_assets,
            cron_schedule="0 18 * * *",
            tags={
                "dagster/priority": "-1",
            },
        ),
        ScheduleDefinition(
            job=materialize_unstable_source_assets,
            cron_schedule="0 12 * * *",
            tags={
                "dagster/priority": "-1",
            },
        ),
        # Run SBOM assets on Tuesday and Friday at midnight, since they take too long
        ScheduleDefinition(
            job=materialize_sbom_source_assets,
            cron_schedule="0 6 * * 2,5",
            tags={
                "dagster/priority": "-1",
            },
        ),
    ]

    jobs: list[FactoryJobDefinition] = [
        materialize_core_assets,
        materialize_stable_source_assets,
        materialize_unstable_source_assets,
        materialize_sbom_source_assets,
        materialize_sqlmesh_assets,
    ]

    if global_config.sqlmesh_assets_on_default_code_location_enabled:
        sqlmesh_and_downstream_assets = define_asset_job(
            "sqlmesh_and_downstream_assets",
            sqlmesh_source_downstream_tag,
            description="Materializes all of sqlmesh and any assets downstream of sqlmesh",
        )

        # Run sqlmesh assets daily, but only materialize downstream assets every
        # first or fifteenth of a month. Due to the nessie commit that is
        # required to publish the final dataset, this should be a safe operation
        @dg.schedule(job_name="sqlmesh_all_assets", cron_schedule="0 5 * * *")
        def daily_sqlmesh_materialization_schedule():
            if is_first_or_fifteenth_of_the_month():
                return dg.SkipReason(
                    skip_message="On first or fifteenth of the month we run sqlmesh and downstream assets. Skipping this duplicate run."
                )
            return dg.RunRequest(
                job_name="sqlmesh_all_assets",
            )

        @dg.schedule(target=sqlmesh_and_downstream_assets, cron_schedule="0 5 1,15 * *")
        def twice_monthly_sqlmesh_and_downstream_materialization_schedule():
            if is_first_or_fifteenth_of_the_month():
                return dg.RunRequest(
                    job_name="sqlmesh_and_downstream_assets",
                )

            return dg.SkipReason(
                skip_message="Not on first or fifteenth of the month, skipping sqlmesh and downstream assets"
            )

        schedules.append(daily_sqlmesh_materialization_schedule)
        schedules.append(twice_monthly_sqlmesh_and_downstream_materialization_schedule)
        jobs.append(sqlmesh_and_downstream_assets)

    return AssetFactoryResponse(
        assets=[],
        jobs=jobs,
        schedules=schedules,
    )
