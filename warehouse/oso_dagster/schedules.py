"""
To add a daily schedule that materializes your dbt assets, uncomment the following lines.
"""

from dagster import define_asset_job, ScheduleDefinition, AssetSelection

materialize_all_assets = define_asset_job(
    "materialize_all_assets_job", AssetSelection.all()
)

materialize_source_assets = define_asset_job(
    "materialize_source_assets_job",
    AssetSelection.tag("opensource.observer/type", "source"),
)

schedules = [
    # Run everything once a week on sunday at midnight
    ScheduleDefinition(
        job=materialize_all_assets,
        cron_schedule="0 0 * * 0",
    ),
    # Run only source data every day (exclude sunday as it's already in the schedule above)
    ScheduleDefinition(
        job=materialize_source_assets,
        cron_schedule="0 0 * * 1-6",
    ),
]
