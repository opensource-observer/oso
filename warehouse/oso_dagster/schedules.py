from typing import Generator, Iterable, List, cast

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
from oso_dagster.factories.common import AssetFactoryResponse

partitioned_assets = AssetSelection.tag(
    "opensource.observer/extra", "partitioned-assets"
)

core_sources_tag = AssetSelection.tag("opensource.observer/source", "core")

unstable_sources_tag = AssetSelection.tag("opensource.observer/source", "unstable")

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

materialize_source_assets = define_asset_job(
    "materialize_source_assets_job",
    AssetSelection.tag("opensource.observer/type", "source")
    | AssetSelection.tag("opensource.observer/type", "source-qa")
    | core_sources_tag,
)

materialize_unstable_source_assets = define_asset_job(
    "materialize_unstable_source_assets_job",
    unstable_sources_tag,
)

materialize_core_assets = define_asset_job(
    "materialize_core_assets_job",
    AssetSelection.all() - core_sources_tag - unstable_sources_tag - partitioned_assets,
)

schedules: list[ScheduleDefinition] = [
    # Run core pipeline assets once a week on sunday at midnight
    ScheduleDefinition(
        job=materialize_core_assets,
        cron_schedule="0 0 * * 0",
        tags={
            "dagster/priority": "-1",
        },
    ),
    ScheduleDefinition(
        job=materialize_source_assets,
        cron_schedule="0 0 * * 0",
        tags={
            "dagster/priority": "-1",
        },
    ),
    ScheduleDefinition(
        job=materialize_unstable_source_assets,
        cron_schedule="0 0 * * 0",
        tags={
            "dagster/priority": "-1",
        },
    ),
]
