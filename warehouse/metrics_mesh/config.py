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
)

dotenv.load_dotenv()

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
        "clickhouse": GatewayConfig(
            connection=ClickhouseConnectionConfig(
                host=os.environ.get("SQLMESH_CLICKHOUSE_HOST", ""),
                username=os.environ.get("SQLMESH_CLICKHOUSE_USERNAME", ""),
                password=os.environ.get("SQLMESH_CLICKHOUSE_PASSWORD", ""),
                port=int(os.environ.get("SQLMESH_CLICKHOUSE_PORT", "443")),
                concurrent_tasks=int(
                    os.environ.get("SQLMESH_CLICKHOUSE_CONCURRENT_TASKS", "8")
                ),
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
