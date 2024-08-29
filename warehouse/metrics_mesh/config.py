import os
import dotenv

from sqlmesh.core.config import (
    Config,
    ModelDefaultsConfig,
    GatewayConfig,
    DuckDBConnectionConfig,
)
from sqlmesh.core.config.connection import ClickhouseConnectionConfig

dotenv.load_dotenv()

config = Config(
    model_defaults=ModelDefaultsConfig(dialect="postgres", start="2024-08-01"),
    gateways={
        "local": GatewayConfig(
            connection=DuckDBConnectionConfig(
                database=os.environ["SQLMESH_DUCKDB_LOCAL_PATH"]
            ),
        ),
        "clickhouse": GatewayConfig(
            connection=ClickhouseConnectionConfig(
                host=os.environ["SQLMESH_CLICKHOUSE_HOST"],
                username=os.environ["SQLMESH_CLICKHOUSE_USERNAME"],
                password=os.environ["SQLMESH_CLICKHOUSE_PASSWORD"],
                port=int(os.environ["SQLMESH_CLICKHOUSE_PORT"]),
            ),
            state_connection=DuckDBConnectionConfig(
                database=os.environ["SQLMESH_DUCKDB_STATE_PATH"]
            ),
        ),
    },
    default_gateway="local",
    variables={"fulltime_dev_days": 10, "activity_window": 30},
)
