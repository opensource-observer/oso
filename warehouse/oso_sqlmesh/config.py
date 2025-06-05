import os
import sys

import dotenv
from metrics_tools.models import constants
from metrics_tools.source.rewrite import (
    LOCAL_TRINO_DOCKER_REWRITE_RULES,
    LOCAL_TRINO_REWRITE_RULES,
)
from sqlmesh.core.config import (
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    LinterConfig,
    ModelDefaultsConfig,
)
from sqlmesh.core.config.connection import (
    GCPPostgresConnectionConfig,
    PostgresConnectionConfig,
    TrinoConnectionConfig,
)

dotenv.load_dotenv()

# SOMETHING broke with the executable path for the sqlmesh package
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURR_DIR))

config = Config(
    linter=LinterConfig(
        enabled=True,
        rules={
            "incrementalmusthavetimepartition",
            "incrementalmustdefinenogapsaudit",
            "incrementalmusthavelookback",
            "incrementalmusthaveforwardonly",
            "timepartitionsmustbebucketed",
            "nomissingaudits",
            "entitycategorytagrequired",
        },
    ),
    default_test_connection=(
        DuckDBConnectionConfig(
            concurrent_tasks=1,
            database=os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH"),
        )
        if os.environ.get("SQLMESH_DEBUG_TESTS")
        else None
    ),
    model_defaults=ModelDefaultsConfig(dialect="trino", start="2024-08-01"),
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
                catalog=os.environ.get("SQLMESH_TRINO_CATALOG", "iceberg"),
                concurrent_tasks=int(
                    os.environ.get("SQLMESH_TRINO_CONCURRENT_TASKS", "8")
                ),
                retries=int(os.environ.get("SQLMESH_TRINO_RETRIES", "5")),
            ),
            state_connection=DuckDBConnectionConfig(
                concurrent_tasks=1,
                database=os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH"),
            ),
            variables={
                "oso_source_rewrite": LOCAL_TRINO_REWRITE_RULES,
            },
        ),
        "local-trino-docker": GatewayConfig(
            connection=TrinoConnectionConfig(
                host=os.environ.get("SQLMESH_TRINO_HOST", "localhost"),
                port=int(os.environ.get("SQLMESH_TRINO_PORT", "8080")),
                http_scheme="http",
                user=os.environ.get("SQLMESH_TRINO_USER", "sqlmesh"),
                catalog=os.environ.get("SQLMESH_TRINO_CATALOG", "iceberg"),
                concurrent_tasks=int(
                    os.environ.get("SQLMESH_TRINO_CONCURRENT_TASKS", "8")
                ),
                retries=int(os.environ.get("SQLMESH_TRINO_RETRIES", "5")),
            ),
            state_connection=PostgresConnectionConfig(
                host=os.environ.get("SQLMESH_POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("SQLMESH_POSTGRES_PORT", "5432")),
                user=os.environ.get("SQLMESH_POSTGRES_USER", "postgres"),
                password=os.environ.get("SQLMESH_POSTGRES_PASSWORD", "postgres"),
                database=os.environ.get("SQLMESH_POSTGRES_DB", "postgres"),
            ),
            variables={
                "oso_source_rewrite": LOCAL_TRINO_DOCKER_REWRITE_RULES,
            },
        ),
        "trino": GatewayConfig(
            connection=TrinoConnectionConfig(
                host=os.environ.get("SQLMESH_TRINO_HOST", "localhost"),
                port=int(os.environ.get("SQLMESH_TRINO_PORT", "8080")),
                http_scheme="http",
                user=os.environ.get("SQLMESH_TRINO_USER", "sqlmesh"),
                catalog=os.environ.get("SQLMESH_TRINO_CATALOG", "iceberg"),
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
    variables={
        "fulltime_dev_days": 10,
        "activity_window": 30,
        "blockchain_incremental_start": constants.blockchain_incremental_start,
        "deps_dev_incremental_start": constants.deps_dev_incremental_start,
        "github_incremental_start": constants.github_incremental_start,
        "funding_incremental_start": constants.funding_incremental_start,
        "defillama_incremental_start": constants.defillama_incremental_start,
        "testing_enabled": constants.testing_enabled,
        "superchain_audit_start": constants.superchain_audit_start,
        # Generally this should always be set to now but if there are issues
        # with the superchain data then this can be set to a specific date to
        # avoid breaking the entire pipeline. That should only be used in
        # extenuating circumstances.
        #"superchain_audit_end": "now",
        "superchain_audit_end": "2025-05-26 00:00:00",
    },
)
