import logging
import typing as t
from contextlib import contextmanager
from datetime import datetime

import duckdb
import psycopg2
from google.cloud import bigquery
from pydantic import BaseModel, Field
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


class RowRestriction(BaseModel):
    time_column: str = ""
    # Other expressions that are used in the row restriction. These are joined
    # using `AND`
    wheres: t.List[str] = []

    def as_str(self, start: datetime, end: datetime, dialect: str = "bigquery") -> str:
        where_expressions: t.List[exp.Expression] = []
        if self.time_column:
            where_expressions.append(
                exp.GTE(
                    this=exp.to_column(self.time_column),
                    expression=exp.Literal(
                        this=start.strftime("%Y-%m-%d"), is_string=True
                    ),
                )
            )
            where_expressions.append(
                exp.LT(
                    this=exp.to_column(self.time_column),
                    expression=exp.Literal(
                        this=end.strftime("%Y-%m-%d"), is_string=True
                    ),
                )
            )
        additional_where_expressions = [parse_one(where) for where in self.wheres]
        where_expressions.extend(additional_where_expressions)
        return " AND ".join([ex.sql(dialect=dialect) for ex in where_expressions])

    def has_restriction(self) -> bool:
        return bool(self.time_column or self.wheres)


class TableMappingDestination(BaseModel):
    row_restriction: RowRestriction = Field(default_factory=lambda: RowRestriction())
    table: str = ""

    def has_restriction(self) -> bool:
        if self.row_restriction:
            return self.row_restriction.has_restriction()
        return False


TableMappingConfig = t.Dict[str, str | TableMappingDestination]


class DestinationLoader(t.Protocol):
    def load_from_bq(
        self,
        start: datetime,
        end: datetime,
        source_name: str,
        destination: TableMappingDestination,
    ): ...

    def drop_all(self): ...

    def drop_non_sources(self): ...

    def sqlmesh(self, extra_args: t.List[str], extra_env: t.Dict[str, str]): ...


class BaseLoaderConfig(BaseModel):
    @contextmanager
    def loader(
        self, config: "Config", bq_client: bigquery.Client
    ) -> t.Iterator[DestinationLoader]: ...


class DuckDbLoaderConfig(BaseLoaderConfig):
    type: t.Literal["duckdb"] = "duckdb"
    duckdb_path: str

    def duckdb_connect(self):
        return duckdb.connect(self.duckdb_path)

    @contextmanager
    def loader(self, config: "Config", bq_client: bigquery.Client):
        from metrics_tools.local.loader import DuckDbDestinationLoader

        yield DuckDbDestinationLoader(config, bq_client, self.duckdb_connect())


class LocalTrinoLoaderConfig(BaseModel):
    type: t.Literal["local-trino"] = "local-trino"
    duckdb_path: str

    postgres_db: str = "postgres"
    postgres_user: str = "postgres"
    postgres_password: str = "password"

    postgres_k8s_service: str = "trino-psql-postgresql"
    postgres_k8s_namespace: str = "local-trino-psql"
    postgres_k8s_port: int = 5432

    trino_k8s_service: str = "local-trino-trino"
    trino_k8s_namespace: str = "local-trino"
    trino_k8s_port: int = 8080

    def postgres_connection_string(self, port: int) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@localhost:{port}/{self.postgres_db}"

    def postgres_connect(self, port: int):
        return psycopg2.connect(
            database=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            host="localhost",
            port=port,
        )

    def duckdb_connect(self):
        return duckdb.connect(self.duckdb_path)

    @contextmanager
    def loader(self, config: "Config", bq_client: bigquery.Client):
        from kr8s.objects import Service
        from metrics_tools.local.loader import LocalTrinoDestinationLoader

        postgres_service = t.cast(
            Service,
            Service.get(
                name=self.postgres_k8s_service, namespace=self.postgres_k8s_namespace
            ),
        )

        with postgres_service.portforward(
            remote_port=self.postgres_k8s_port
        ) as local_port:  # type: ignore
            logger.debug(f"Proxied postgres to port: {local_port}")
            yield LocalTrinoDestinationLoader(
                config,
                bq_client,
                self.duckdb_connect(),
                self.postgres_connect(local_port),
                "localhost",
                local_port,
            )


LoaderTypes = t.Union[DuckDbLoaderConfig, LocalTrinoLoaderConfig]


class LoaderConfig(BaseModel):
    type: str
    config: LoaderTypes = Field(discriminator="type")


class Config(BaseModel):
    table_mapping: TableMappingConfig
    repo_dir: str
    max_days: int = 7
    max_results_per_query: int = 0
    project_id: str = "opensource-observer"
    timeseries_start: str = "2024-12-01"
    loader: LoaderConfig

    def loader_instance(self):
        return self.loader.config.loader(self, bigquery.Client())
