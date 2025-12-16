import logging
import typing as t
from contextlib import asynccontextmanager

from dlt.common.destination import Destination
from oso_dagster.resources.trino import TrinoResource

if t.TYPE_CHECKING:
    from scheduler.config import CommonSettings

logger = logging.getLogger(__name__)


class DLTDestinationResource:
    def __init__(
        self,
        *,
        common_settings: "CommonSettings",
        trino: TrinoResource | None,
    ) -> None:
        self._common_settings = common_settings
        self._trino = trino

    @asynccontextmanager
    async def get_destination(
        self, *, dataset_schema: str
    ) -> t.AsyncIterator[Destination]:
        if not self._common_settings.trino_enabled:
            from dlt.destinations import duckdb
            from dlt.destinations.impl.duckdb.configuration import DuckDbCredentials

            yield duckdb(
                credentials=DuckDbCredentials(
                    conn_or_path=self._common_settings.local_duckdb_path,
                )
            )
            return

        if not self._trino:
            raise ValueError("Trino is enabled but no TrinoResource was provided.")

        from dlt.destinations import sqlalchemy

        catalog = "iceberg"

        async with self._trino.async_get_client(log_override=logger) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                f"CREATE SCHEMA IF NOT EXISTS {catalog}.{dataset_schema}"
            )
            user = conn.user or "scheduler"
            credentials = (
                f"trino://{user}@{conn.host}:{conn.port}/{catalog}/{dataset_schema}"
            )
            yield sqlalchemy(credentials=credentials, destination_name="trino")
