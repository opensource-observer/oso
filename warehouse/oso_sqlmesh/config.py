import os

import dotenv
from sqlmesh.core.config import (
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
)
from sqlmesh.core.config.connection import (
    GCPPostgresConnectionConfig,
    TrinoConnectionConfig,
)

dotenv.load_dotenv()

config = Config(
    model_defaults=ModelDefaultsConfig(dialect="duckdb", start="2024-08-01"),
    gateways={
        "local": GatewayConfig(
            connection=DuckDBConnectionConfig(
                concurrent_tasks=1,
                database=os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH"),
            ),
        ),
        # This is a local trino gateway that connects to a local trino deployed
        # onto a kind cluster. It also uses duckdb for state storage as opposed
        # to using postgres.
        "local-trino": GatewayConfig(
            connection=TrinoConnectionConfig(
                host=os.environ.get("SQLMESH_TRINO_HOST", "localhost"),
                port=int(os.environ.get("SQLMESH_TRINO_PORT", "8080")),
                http_scheme="http",
                user=os.environ.get("SQLMESH_TRINO_USER", "sqlmesh"),
                catalog=os.environ.get("SQLMESH_TRINO_CATALOG", "metrics"),
                concurrent_tasks=int(
                    os.environ.get("SQLMESH_TRINO_CONCURRENT_TASKS", "8")
                ),
                retries=int(os.environ.get("SQLMESH_TRINO_RETRIES", "5")),
            ),
            state_connection=DuckDBConnectionConfig(
                concurrent_tasks=1,
                database=os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH"),
            ),
        ),
        "trino": GatewayConfig(
            connection=TrinoConnectionConfig(
                host=os.environ.get("SQLMESH_TRINO_HOST", "localhost"),
                port=int(os.environ.get("SQLMESH_TRINO_PORT", "8080")),
                http_scheme="http",
                user=os.environ.get("SQLMESH_TRINO_USER", "sqlmesh"),
                catalog=os.environ.get("SQLMESH_TRINO_CATALOG", "metrics"),
                concurrent_tasks=int(
                    os.environ.get("SQLMESH_TRINO_CONCURRENT_TASKS", "64")
                ),
                retries=int(os.environ.get("SQLMESH_TRINO_RETRIES", "5")),
            ),
            state_connection=GCPPostgresConnectionConfig(
                instance_connection_string=os.environ.get(
                    "SQLMESH_POSTGRES_INSTANCE_CONNECTION_STRING", ""
                ),
                user=os.environ.get("SQLMESH_POSTGRES_USER", ""),
                password=os.environ.get("SQLMESH_POSTGRES_PASSWORD", "placeholder"),
                db=os.environ.get("SQLMESH_POSTGRES_DB", ""),
            ),
        ),
    },
    default_gateway="local",
    variables={"fulltime_dev_days": 10, "activity_window": 30},
)
