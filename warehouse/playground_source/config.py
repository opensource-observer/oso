import os
from sqlmesh.core.config import (
    Config,
    ModelDefaultsConfig,
    GatewayConfig,
    BigQueryConnectionConfig,
    DuckDBConnectionConfig,
)

config = Config(
    model_defaults=ModelDefaultsConfig(dialect="bigquery"),
    gateways={
        "local": GatewayConfig(
            state_connection=DuckDBConnectionConfig(database="db.db")
        ),
        "bq": GatewayConfig(
            state_connection=BigQueryConnectionConfig(
                keyfile=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            )
        ),
    },
    default_gateway="local",
)
