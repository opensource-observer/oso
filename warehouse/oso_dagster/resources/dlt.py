from dlt.destinations import bigquery, duckdb, filesystem
from dlt.sources.credentials import GcpServiceAccountCredentials
from oso_dagster.config import DagsterConfig


def load_dlt_staging(global_config: DagsterConfig):
    assert global_config.staging_bucket_url is not None
    return filesystem(bucket_url=global_config.staging_bucket_url)


def load_dlt_warehouse_destination(global_config: DagsterConfig):
    if global_config.enable_bigquery:
        assert global_config.project_id
        return bigquery(
            credentials=GcpServiceAccountCredentials(
                project_id=global_config.project_id
            ),
            truncate_tables_on_staging_destination_before_load=False,
        )
    else:
        return duckdb(global_config.local_duckdb_path)
