import abc
import logging
import typing as t
from contextlib import asynccontextmanager

from dlt.common.destination import Destination
from oso_dagster.resources.trino import TrinoResource

logger = logging.getLogger(__name__)


class DLTDestinationResource(abc.ABC):
    """Abstract base class for DLT destination resources."""

    @abc.abstractmethod
    @asynccontextmanager
    def get_destination(
        self, *, dataset_schema: str, user: str | None = None
    ) -> t.AsyncIterator[Destination]:
        """Get a DLT destination configured for the given dataset schema."""
        ...


class DuckDBDLTDestinationResource(DLTDestinationResource):
    """DLT destination resource for DuckDB."""

    def __init__(self, *, database_path: str) -> None:
        self._database_path = database_path

    @asynccontextmanager
    async def get_destination(
        self, *, dataset_schema: str, user: str | None = None
    ) -> t.AsyncIterator[Destination]:
        from dlt.destinations import duckdb
        from dlt.destinations.impl.duckdb.configuration import DuckDbCredentials

        yield duckdb(
            credentials=DuckDbCredentials(
                conn_or_path=self._database_path,
            ),
            enable_dataset_name_normalization=False,
        )


class TrinoDLTDestinationResource(DLTDestinationResource):
    """DLT destination resource for Trino."""

    def __init__(self, *, trino: TrinoResource, catalog: str) -> None:
        self._trino = trino
        self._catalog = catalog

    @asynccontextmanager
    async def get_destination(
        self, *, dataset_schema: str, user: str | None = None
    ) -> t.AsyncIterator[Destination]:
        from dlt.destinations import sqlalchemy

        async with self._trino.async_get_client(log_override=logger) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                f'CREATE SCHEMA IF NOT EXISTS "{self._catalog}"."{dataset_schema}"'
            )
            user = user or conn.user or "scheduler"
            credentials = f"trinoso://{user}@{conn.host}:{conn.port}/{self._catalog}/{dataset_schema}"
            yield sqlalchemy(
                credentials=credentials,
                destination_name="trino",
                enable_dataset_name_normalization=False,
            )
