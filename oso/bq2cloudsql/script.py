import os
from google.cloud import bigquery, storage

from .synchronizer import BigQueryCloudSQLSynchronizer
from .cloudsql import CloudSQLClient


def run():
    bq = bigquery.Client()
    storage_client = storage.Client()
    cloudsql = CloudSQLClient.connect('oso-production', 'us-central1', 'oso-dw-test', 'postgres', os.environ.get('CLOUDSQL_PASSWORD'), 'postgres')

    synchronizer = BigQueryCloudSQLSynchronizer(
        bq, 
        storage_client,
        cloudsql,
        'oso-production', 
        'opensource_observer', 
        {
            "all_events_by_project": "all_events_by_project"
        }, 
        'oso-csv-exports'
    )
    synchronizer.sync()