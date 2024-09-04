import os
import dotenv
import typing as t

from pydantic import Field
from sqlmesh.core.config import (
    Config,
    ModelDefaultsConfig,
    GatewayConfig,
    DuckDBConnectionConfig,
)
from sqlmesh import EngineAdapter
from sqlmesh.core.engine_adapter.clickhouse import ClickhouseEngineAdapter
from sqlmesh.core.config.connection import (
    ConnectionConfig,
    ClickhouseConnectionConfig,
    GCPPostgresConnectionConfig,
)

dotenv.load_dotenv()


class ChDBConnectionConfig(ConnectionConfig):
    """
    Clickhouse Connection Configuration.

    Property reference: https://clickhouse.com/docs/en/integrations/python#client-initialization
    """

    path: str | None

    type_: t.Literal["chdb"] = Field(alias="type", default="chdb")
    concurrent_tasks: t.Literal[1] = 1
    register_comments: bool = True
    pre_ping: t.Literal[False] = False

    @property
    def _connection_kwargs_keys(self) -> t.Set[str]:
        kwargs = {
            "path",
        }
        return kwargs

    @property
    def _engine_adapter(self) -> t.Type[EngineAdapter]:
        return ClickhouseEngineAdapter

    @property
    def _connection_factory(self) -> t.Callable:
        from chdb.dbapi import connect  # type: ignore

        return connect

    @property
    def _static_connection_kwargs(self) -> t.Dict[str, t.Any]:
        from sqlmesh import __version__

        return {"client_name": f"SQLMesh/{__version__}"}


config = Config(
    model_defaults=ModelDefaultsConfig(dialect="clickhouse", start="2024-08-01"),
    gateways={
        "local": GatewayConfig(
            connection=DuckDBConnectionConfig(
                database=os.environ.get("SQLMESH_DUCKDB_LOCAL_PATH")
            ),
        ),
        "local-chdb": GatewayConfig(
            connection=ChDBConnectionConfig(
                path=os.environ.get("SQLMESH_CHDB_LOCAL_PATH"),
            )
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
                password=os.environ.get("SQLMESH_POSTGRES_PASSWORD", "placeholder"),
                db=os.environ.get("SQLMESH_POSTGRES_DB", ""),
            ),
        ),
    },
    default_gateway="local",
    variables={"fulltime_dev_days": 10, "activity_window": 30},
)
