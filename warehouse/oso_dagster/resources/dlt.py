from .. import constants
from dlt.destinations import filesystem, bigquery, duckdb
from dlt.sources.credentials import GcpServiceAccountCredentials


def load_dlt_staging():
    assert constants.staging_bucket is not None
    return filesystem(bucket_url=constants.staging_bucket)


def load_dlt_warehouse_destination():
    if constants.enable_bigquery:
        assert constants.project_id
        return bigquery(
            credentials=GcpServiceAccountCredentials(project_id=constants.project_id)
        )
    else:
        return duckdb(constants.local_duckdb)
