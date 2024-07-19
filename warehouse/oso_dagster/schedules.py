"""
To add a daily schedule that materializes your dbt assets, uncomment the following lines.
"""

from dagster import define_asset_job, ScheduleDefinition, AssetSelection

materialize_all_assets = define_asset_job(
    "materialize_all_assets_job", AssetSelection.all()
)

schedules = [
    ScheduleDefinition(
        job=materialize_all_assets,
        cron_schedule="@daily",
    )
]
