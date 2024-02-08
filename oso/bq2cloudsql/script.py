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
                'all_events_daily_to_project',
                'events_daily_to_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_monthly_to_project',
                'events_monthly_to_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_weekly_to_project',
                'events_weekly_to_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_daily_from_project',
                'events_daily_from_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_monthly_from_project',
                'events_monthly_from_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_weekly_from_project',
                'events_weekly_from_project'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_daily_to_artifact',
                'events_daily_to_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_monthly_to_artifact',
                'events_monthly_to_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_weekly_to_artifact',
                'events_weekly_to_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_daily_from_artifact',
                'events_daily_from_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_monthly_from_artifact',
                'events_monthly_from_artifact'
            ),
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                'all_events_weekly_from_artifact',
                'events_weekly_from_artifact'
            ),
        ],
        'oso-csv-exports'
    )
    synchronizer.sync()