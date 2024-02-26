import os
import json
from typing import List

from google.cloud import bigquery, storage
from dbt.cli.main import dbtRunner, dbtRunnerResult

from .synchronizer import BigQueryCloudSQLSynchronizer, TableSyncConfig, TableSyncMode
from .cloudsql import CloudSQLClient

from dotenv import load_dotenv


def table_sync_config_from_dbt_marts(target: str) -> List[TableSyncConfig]:
    dbt = dbtRunner()
    r: dbtRunnerResult = dbt.invoke(
        [
            "ls",
            "--output",
            "json",
            "--select",
            "marts.*",
            "--target",
            target,
            "--resource-type",
            "model",
        ]
    )
    if not r.success:
        raise Exception("dbt listing failed")
    if not isinstance(r.result, list):
        raise Exception("Unexpected response from dbt")
    model_configs = map(lambda a: json.loads(a), r.result)
    sync_configs: List[TableSyncConfig] = []
    for config in model_configs:
        print(config["name"])
        sync_configs.append(
            TableSyncConfig(
                TableSyncMode.OVERWRITE,
                config["name"],
                config["name"],
            )
        )
    return sync_configs


def run():
    load_dotenv()
    bq = bigquery.Client()
    storage_client = storage.Client()
    cloudsql = CloudSQLClient.connect(
        os.environ.get("GOOGLE_PROJECT_ID"),
        os.environ.get("CLOUDSQL_REGION"),
        os.environ.get("CLOUDSQL_INSTANCE_ID"),
        os.environ.get("CLOUDSQL_DB_USER"),
        os.environ.get("CLOUDSQL_DB_PASSWORD"),
        os.environ.get("CLOUDSQL_DB_NAME"),
    )

    # Automtically discover dbt marts
    table_sync_configs = table_sync_config_from_dbt_marts(os.environ.get("DBT_TARGET"))

    synchronizer = BigQueryCloudSQLSynchronizer(
        bq,
        storage_client,
        cloudsql,
        os.environ.get("GOOGLE_PROJECT_ID"),
        os.environ.get("BIGQUERY_DATASET_ID"),
        table_sync_configs,
        os.environ.get("CLOUDSTORAGE_BUCKET_NAME"),
    )
    synchronizer.sync()
