import logging
from contextlib import asynccontextmanager, contextmanager

import duckdb
from dagster import ConfigurableResource, ResourceDependency
from metrics_tools.transfer.duckdb import DuckDBExporter
from oso_dagster.resources.storage import GCSTimeOrderedStorageResource
from pydantic import Field

logger = logging.getLogger(__name__)


class DuckDBResource(ConfigurableResource):
    """Resource for interacting with DuckDB."""

    database_path: str = Field(
        default=":memory:", description="Path to the DuckDB database file."
    )

    @contextmanager
    def get_connection(self):
        """Provides a DuckDB connection."""
        logger.info("Opening DuckDB connection.")
        conn = duckdb.connect(database=self.database_path)
        try:
            yield conn
        finally:
            logger.info("Closing DuckDB connection.")
            conn.close()


class DuckDBExporterResource(ConfigurableResource):
    """Resource for providing a DuckDBExporter instance."""

    duckdb: ResourceDependency[DuckDBResource]
    time_ordered_storage: ResourceDependency[GCSTimeOrderedStorageResource]

    @asynccontextmanager
    async def get(self, export_prefix: str, gcs_bucket_name: str):
        """Provides the DuckDB connection for queries."""
        async with self.time_ordered_storage.get(export_prefix) as storage:
            with self.duckdb.get_connection() as conn:
                exporter = DuckDBExporter(
                    storage, conn, gcs_bucket_name=gcs_bucket_name
                )
                yield exporter
