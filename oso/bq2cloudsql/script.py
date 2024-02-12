import os
from google.cloud import bigquery, storage

from .synchronizer import BigQueryCloudSQLSynchronizer, TableSyncConfig, TableSyncMode
from .cloudsql import CloudSQLClient

from dotenv import load_dotenv


def run():
    load_dotenv()
    bq = bigquery.Client()
    storage_client = storage.Client()
    cloudsql = CloudSQLClient.connect(
        os.environ.get('GOOGLE_PROJECT_ID'), 
        os.environ.get('CLOUDSQL_REGION'), 
        os.environ.get('CLOUDSQL_INSTANCE_ID'), 
        os.environ.get('CLOUDSQL_DB_USER'), 
        os.environ.get('CLOUDSQL_PASSWORD'), 
        os.environ.get('CLOUDSQL_DB_NAME')
    )

    synchronizer = BigQueryCloudSQLSynchronizer(
        bq, 
        storage_client,
        cloudsql,
        'oso-production', 
        'opensource_observer', 
        [
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_daily_to_project',
                'bq_events_daily_to_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_monthly_to_project',
                'bq_events_monthly_to_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_weekly_to_project',
                'bq_events_weekly_to_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_daily_from_project',
                'bq_events_daily_from_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_monthly_from_project',
                'bq_events_monthly_from_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_weekly_from_project',
                'bq_events_weekly_from_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_daily_to_artifact',
                'bq_events_daily_to_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_monthly_to_artifact',
                'bq_events_monthly_to_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_weekly_to_artifact',
                'bq_events_weekly_to_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_daily_from_artifact',
                'bq_events_daily_from_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_monthly_from_artifact',
                'bq_events_monthly_from_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'events_weekly_from_artifact',
                'bq_events_weekly_from_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'first_contribution_to_project',
                'bq_first_contribution_to_project',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'last_contribution_to_project',
                'bq_last_contribution_to_project',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'users_monthly_to_project',
                'bq_users_monthly_to_project',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'event_types',
                'bq_event_types',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'artifacts',
                'bq_artifacts',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'projects',
                'bq_projects',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'collections',
                'bq_collections',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'projects_by_collection_slugs',
                'bq_projects_by_collection_slugs',
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'artifacts_by_project_slugs',
                'bq_artifacts_by_project_slugs',
            ),
        ],
        'oso-csv-exports'
    )
    synchronizer.sync()