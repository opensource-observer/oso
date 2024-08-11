from .. import constants
from dagster_polars import PolarsBigQueryIOManager
from dagster_duckdb_polars import DuckDBPolarsIOManager


def load_io_manager():
    if constants.enable_bigquery:
        return PolarsBigQueryIOManager(project=constants.project_id)
    return DuckDBPolarsIOManager(database=constants.local_duckdb)
