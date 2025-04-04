import logging
import os
from typing import Protocol

import duckdb
from aiotrino.dbapi import Connection, connect
from metrics_tools.seed.sql import (
    sql_create_table_from_pydantic_schema,
    sql_insert_from_pydantic_instances,
)
from metrics_tools.seed.types import SeedConfig
from metrics_tools.source.rewrite import DUCKDB_REWRITE_RULES, oso_source_rewrite
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DestinationLoader(Protocol):
    async def close(self): ...

    async def load(self, config: SeedConfig[BaseModel]): ...

    async def create_schema(self, name: str): ...

    async def create_table(self, name: str, base: type[BaseModel]): ...

    async def insert(self, table_name: str, instances: list[BaseModel]): ...


class TrinoLoader(DestinationLoader):
    conn: Connection

    @classmethod
    def connect(cls):
        connection = connect(
            host="localhost",
            port=8080,
            user="user",
        )
        return cls(connection)

    def __init__(self, conn):
        self.conn = conn

    async def close(self):
        await self.conn.close()

    async def load(self, config: SeedConfig[BaseModel]):
        logger.info(f"Loading {config.catalog}.{config.schema}.{config.table}")
        schema = f"{config.catalog}.{config.schema}"
        table = f"{config.catalog}.{config.schema}.{config.table}"
        await self.create_schema(schema)
        await self.create_table(table, config.base)
        await self.insert(table, config.rows)

    async def create_schema(self, name: str):
        logger.info(f"Creating schema {name}")
        cur = await self.conn.cursor()
        await cur.execute(
            f"""
        CREATE SCHEMA IF NOT EXISTS {name}
        """
        )
        await cur.fetchall()

    async def create_table(self, name: str, base: type[BaseModel]):
        logger.info(f"Creating table {name}")
        schema = base.model_json_schema()
        sql = sql_create_table_from_pydantic_schema(name, schema, "trino")
        cur = await self.conn.cursor()
        await cur.execute(sql)
        await cur.fetchall()

    async def insert(self, table_name: str, instances: list[BaseModel]):
        logger.info(f"Inserting {len(instances)} rows into {table_name}")
        sql = sql_insert_from_pydantic_instances(table_name, instances, "trino")
        cur = await self.conn.cursor()
        await cur.execute(sql)
        await cur.fetchall()


class DuckDbLoader(DestinationLoader):
    conn: duckdb.DuckDBPyConnection

    @classmethod
    def connect(cls):
        path = os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH")
        if not path:
            raise ValueError("SQLMESH_DUCKDB_LOCAL_PATH environment variable not set")
        connection = duckdb.connect(path)
        return cls(connection)

    def __init__(self, conn):
        self.conn = conn

    async def close(self):
        self.conn.close()

    async def load(self, config: SeedConfig[BaseModel]):
        logger.info(f"Loading {config.catalog}.{config.schema}.{config.table}")
        table = oso_source_rewrite(
            DUCKDB_REWRITE_RULES, f"{config.catalog}.{config.schema}.{config.table}"
        )
        table_name = table.sql(dialect="duckdb")
        await self.create_schema(table.db)
        await self.create_table(table_name, config.base)
        await self.insert(table_name, config.rows)

    async def create_schema(self, name: str):
        logger.info(f"Creating schema {name}")
        self.conn.sql(
            f"""
        CREATE SCHEMA IF NOT EXISTS {name}
        """
        )

    async def create_table(self, name: str, base: type[BaseModel]):
        logger.info(f"Creating table {name}")
        schema = base.model_json_schema()
        sql = sql_create_table_from_pydantic_schema(name, schema, "duckdb")
        self.conn.sql(sql)

    async def insert(self, table_name: str, instances: list[BaseModel]):
        logger.info(f"Inserting {len(instances)} rows into {table_name}")
        sql = sql_insert_from_pydantic_instances(table_name, instances, "duckdb")
        self.conn.sql(sql)
