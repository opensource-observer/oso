import os

import dotenv
from sqlmesh.core.config import (
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
)
from sqlmesh.core.config.connection import (
    ClickhouseConnectionConfig,
    GCPPostgresConnectionConfig,
    TrinoConnectionConfig,
)

dotenv.load_dotenv()


def pool_manager_factory(config: ClickhouseConnectionConfig):
    from clickhouse_connect.driver import httputil

    return httputil.get_pool_manager(
        num_pools=config.concurrent_tasks,
        max_size=config.concurrent_tasks,
    )


config = Config(
    model_defaults=ModelDefaultsConfig(dialect="clickhouse", start="2024-08-01"),
    gateways={
        "local": GatewayConfig(
            connection=DuckDBConnectionConfig(
                database=os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH")
            ),
            variables={
                "oso_source": "sources",
            },
        ),
        "trino": GatewayConfig(
            connection=TrinoConnectionConfig(
                host="127.0.0.1",
                port=8080,
                http_scheme="http",
                user="sqlmesh",
                catalog="metrics",
                concurrent_tasks=64,
            ),
            state_connection=GCPPostgresConnectionConfig(
                instance_connection_string=os.environ.get(
                    "SQLMESH_POSTGRES_INSTANCE_CONNECTION_STRING", ""
                ),
                user=os.environ.get("SQLMESH_POSTGRES_USER", ""),
                password=os.environ.get("SQLMESH_POSTGRES_PASSWORD", "placeholder"),
                db=os.environ.get("SQLMESH_POSTGRES_DB", ""),
            ),
            variables={
                "oso_source": "default",
            },
        ),
        "clickhouse": GatewayConfig(
            connection=ClickhouseConnectionConfig(
                host=os.environ.get("SQLMESH_CLICKHOUSE_HOST", ""),
                username=os.environ.get("SQLMESH_CLICKHOUSE_USERNAME", ""),
                password=os.environ.get("SQLMESH_CLICKHOUSE_PASSWORD", ""),
                port=int(os.environ.get("SQLMESH_CLICKHOUSE_PORT", "443")),
                concurrent_tasks=int(
                    os.environ.get("SQLMESH_CLICKHOUSE_CONCURRENT_TASKS", "16")
                ),
                send_receive_timeout=1800,
                # connection_settings={"allow_nondeterministic_mutations": 1},
                connection_pool_options={
                    "maxsize": 24,
                    "retries": 0,
                },
            ),
            state_connection=GCPPostgresConnectionConfig(
                instance_connection_string=os.environ.get(
                    "SQLMESH_POSTGRES_INSTANCE_CONNECTION_STRING", ""
                ),
                user=os.environ.get("SQLMESH_POSTGRES_USER", ""),
                password=os.environ.get("SQLMESH_POSTGRES_PASSWORD", "placeholder"),
                db=os.environ.get("SQLMESH_POSTGRES_DB", ""),
            ),
            variables={"oso_source": "default"},
        ),
    },
    default_gateway="local",
    variables={"fulltime_dev_days": 10, "activity_window": 30},
)
