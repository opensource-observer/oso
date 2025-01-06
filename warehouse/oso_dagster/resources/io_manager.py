from dagster_duckdb_polars import DuckDBPolarsIOManager
from dagster_polars import PolarsBigQueryIOManager
from oso_dagster.config import DagsterConfig


def load_io_manager(global_config: DagsterConfig):
    if global_config.enable_bigquery:
        return PolarsBigQueryIOManager(project=global_config.project_id)
    return DuckDBPolarsIOManager(database=global_config.local_duckdb_path)
