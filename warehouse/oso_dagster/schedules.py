"""
To add a daily schedule that materializes your dbt assets, uncomment the following lines.
"""

from dagster import define_asset_job, ScheduleDefinition, AssetSelection

full_sync = define_asset_job("run_everything_job", AssetSelection.all())

schedules = [
    ScheduleDefinition(
        job=full_sync,
        cron_schedule="@daily",
    )
]
