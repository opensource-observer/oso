"""Provides SQLMesh engine adapters as a resource for Dagster assets"""

import logging
import os
import typing as t
from contextlib import asynccontextmanager

import dagster as dg
from oso_dagster.resources.duckdb import DuckDBResource
from oso_dagster.resources.trino import TrinoResource
from pydantic import Field
from sqlglot import exp
from sqlmesh.core.config.connection import TrinoConnectionConfig
from sqlmesh.core.engine_adapter.base import EngineAdapter

module_logger = logging.getLogger(__name__)


class UserDefinedModelEngineAdapterResource(dg.ConfigurableResource):
    """Base UserDefinedModel engine adapter resource"""

    @asynccontextmanager
    def get_adapter(
        self,
        user: t.Optional[str] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.AsyncGenerator[EngineAdapter, None]:
        raise NotImplementedError(
            "get_client not implemented on the base UserDefinedModelEngineAdapterResource"
        )

    def generate_table(self, org_id: str, dataset_id: str, table_id: str) -> exp.Table:
        raise NotImplementedError("generate_table_name not implemented")


class DuckdbEngineAdapterResource(UserDefinedModelEngineAdapterResource):
    """A DuckDB engine adapter resource for Dagster assets."""

    duckdb: dg.ResourceDependency[DuckDBResource] = Field(
        description="The DuckDB resource to use to ensure availability"
    )

    @asynccontextmanager
    async def get_adapter(
        self,
        user: t.Optional[str] = None,
        log_override: t.Optional[logging.Logger] = None,
    ):
        from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter

        with self.duckdb.get_connection() as conn:
            logger = log_override or module_logger
            logger.info(
                "Setting up DuckDB engine adapter. This is in memory and for testing purposes only."
            )

            adapter = DuckDBEngineAdapter(
                connection_factory_or_pool=lambda: conn,
            )
            yield adapter

    def generate_table(self, org_id: str, dataset_id: str, table_id: str) -> exp.Table:
        return exp.to_table(f"org_{org_id}__ds_{dataset_id}.tbl_{table_id}")


class TrinoEngineAdapterResource(UserDefinedModelEngineAdapterResource):
    """A Trino engine adapter resource for Dagster assets."""

    trino: dg.ResourceDependency[TrinoResource] = Field(
        description="The Trino resource to use to ensure availability"
    )

    http_scheme: t.Literal["http", "https"] = Field(
        default="http", description="The connection scheme to use for Trino connections"
    )

    target_catalog: str = Field(
        default="iceberg", description="The catalog to write to"
    )

    def generate_table(self, org_id: str, dataset_id: str, table_id: str):
        return exp.to_table(
            f"{self.target_catalog}.org_{org_id}__ds_{dataset_id}.tbl_{table_id}"
        )

    @asynccontextmanager
    async def get_adapter(
        self,
        user: t.Optional[str] = None,
        log_override: t.Optional[logging.Logger] = None,
    ) -> t.AsyncGenerator[EngineAdapter, None]:
        logger = log_override or module_logger

        async with self.trino.ensure_available(log_override=logger):
            async with self.trino.async_get_client(
                user=user, log_override=logger
            ) as conn:
                logger.info("Setting up Trino engine adapter")
                connection_config = TrinoConnectionConfig(
                    host=conn.host,
                    port=conn.port,
                    user=conn.user or "udm_admin",
                    catalog=conn.catalog,
                    http_scheme=self.http_scheme,
                )
                yield connection_config.create_engine_adapter(
                    concurrent_tasks=os.cpu_count() or 2
                )
