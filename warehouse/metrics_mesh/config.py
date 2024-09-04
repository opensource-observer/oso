import os
import dotenv

from sqlmesh.core.config import (
    Config,
    ModelDefaultsConfig,
    GatewayConfig,
    DuckDBConnectionConfig,
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
        ),
        "clickhouse": GatewayConfig(
            connection=ClickhouseConnectionConfig(
                host=os.environ.get("SQLMESH_CLICKHOUSE_HOST", ""),
                username=os.environ.get("SQLMESH_CLICKHOUSE_USERNAME", ""),
                password=os.environ.get("SQLMESH_CLICKHOUSE_PASSWORD", ""),
                port=int(os.environ.get("SQLMESH_CLICKHOUSE_PORT", "443")),
            ),
            state_connection=GCPPostgresConnectionConfig(
                instance_connection_string=os.environ.get(
                    "SQLMESH_POSTGRES_INSTANCE_CONNECTION_STRING", ""
                ),
                user=os.environ.get("SQLMESH_POSTGRES_USER", ""),
                password=os.environ.get("SQLMESH_POSTGRES_PASSWORD", ""),
                db=os.environ.get("SQLMESH_POSTGRES_DB", ""),
            ),
        ),
    },
    default_gateway="local",
    variables={"fulltime_dev_days": 10, "activity_window": 30},
)
