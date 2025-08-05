import structlog
from dagster_duckdb_polars import DuckDBPolarsIOManager
from dagster_polars import PolarsBigQueryIOManager
from oso_dagster.config import DagsterConfig

logger = structlog.get_logger(__name__)


def load_io_manager(global_config: DagsterConfig):
    if global_config.enable_bigquery:
        logger.info("Using PolarsBigQueryIOManager")
        return PolarsBigQueryIOManager(project=global_config.project_id)

    logger.info("Using DuckDBPolarsIOManager")
    return DuckDBPolarsIOManager(database=global_config.local_duckdb_path)
