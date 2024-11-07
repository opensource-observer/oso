"""A python arrow service that is used to as a proxy to the cluster of compute for the
metrics tools. This allows us to change the underlying compute infrastructure
while maintaining the same interface to the sqlmesh runner.
"""

import logging
import typing as t
import json
import click
from metrics_tools.compute.cluster import start_duckdb_cluster
from metrics_tools.compute.worker import MetricsWorkerPlugin
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.runner import FakeEngineAdapter, MetricsRunner
import pyarrow as pa
import pyarrow.flight as fl
import asyncio
import pandas as pd
import threading
import aiotrino
from trino.dbapi import Connection as Connection
from aiotrino.dbapi import Connection as AsyncConnection
import abc
from pydantic import BaseModel
from datetime import datetime
from dask.distributed import Client, get_worker, Future, as_completed
from dask_kubernetes.operator import KubeCluster, make_cluster_spec


logger = logging.getLogger(__name__)


type_mapping = {
    "INTEGER": "int64",
    "BIGINT": "int64",
    "SMALLINT": "int32",
    "NUMERIC": "float64",
    "REAL": "float32",
    "DOUBLE PRECISION": "float64",
    "VARCHAR": "object",
    "TEXT": "object",
    "BOOLEAN": "bool",
    "DATE": "datetime64[ns]",
    "TIMESTAMP": "datetime64[ns]",
    # Add more mappings as needed
}

arrow_type_mapping = {
    "INTEGER": pa.int32(),
    "BIGINT": pa.int64(),
    "SMALLINT": pa.int16(),
    "NUMERIC": pa.float64(),
    "REAL": pa.float32(),
    "DOUBLE PRECISION": pa.float64(),
    "VARCHAR": pa.string(),
    "TEXT": pa.string(),
    "BOOLEAN": pa.bool_(),
    "DATE": pa.date32(),
    "TIMESTAMP": pa.timestamp("ns"),
}


class QueryInput(BaseModel):
    query_str: str
    start: datetime
    end: datetime
    dialect: str
    columns: t.List[t.Tuple[str, str]]
    ref: PeerMetricDependencyRef
    locals: t.Dict[str, t.Any]
    dependent_tables_map: t.Dict[str, str]

    def to_ticket(self) -> fl.Ticket:
        return fl.Ticket(self.model_dump_json())

    def to_column_names(self) -> pd.Series:
        return pd.Series(list(map(lambda a: a[0], self.columns)))

    def to_arrow_schema(self) -> pa.Schema:
        schema_input = [
            (col_name, arrow_type_mapping[col_type])
            for col_name, col_type in self.columns
        ]
        print(schema_input)
        return pa.schema(schema_input)

    # def coerce_datetimes(self, df: pd.DataFrame) -> pd.DataFrame:
    #     for col_name, col_type in self.columns:
    #         if col_type ==


class Engine(abc.ABC):
    async def run_query(self, query: str, columns: pd.Series) -> pd.DataFrame:
        raise NotImplementedError("run_query not implemented")


class TrinoEngine(Engine):
    @classmethod
    def create(cls, host: str, port: int, user: str, catalog: str):
        async_conn = aiotrino.dbapi.connect(
            host=host,
            port=port,
            user=user,
            catalog=catalog,
        )
        return cls(async_conn)

    def __init__(self, async_conn: AsyncConnection):
        self._async_conn = async_conn

    async def run_query(self, query: str, columns: pd.Series) -> pd.DataFrame:
        cursor = await self._async_conn.cursor()
        await cursor.execute(query)
        results = t.cast(t.List, await cursor.fetchall())
        return pd.DataFrame(results, columns=columns)


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def run_coroutine_in_thread(coro):
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=start_loop, args=(loop,))
    thread.start()


async def my_coroutine():
    # Your asynchronous code here
    await asyncio.sleep(1)
    print("Hello from coroutine in a separate thread!")


async def async_gen_batch(engine: Engine, query: str, columns: pd.Series):
    return await engine.run_query(query, columns)


def execute_duckdb_load(query: str, dependencies: t.Dict[str, str]):
    worker = get_worker()
    plugin = t.cast(MetricsWorkerPlugin, worker.plugins["duckdb-gcs"])
    for ref, actual in dependencies.items():
        plugin.get_for_cache(ref, actual)
    conn = plugin.connection
    return conn.execute(query).df()


class MetricsCalculatorFlightServer(fl.FlightServerBase):
    def __init__(
        self,
        cluster: KubeCluster,
        engine: Engine,
        location: str = "grpc://0.0.0.0:8815",
    ):
        super().__init__(location)
        self.data = pa.Table.from_pydict({"col1": [1, 2, 3]})
        self.loop_loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(
            target=start_loop,
            args=(self.loop_loop,),
        )
        self.loop_thread.start()
        self.engine = engine
        self.cluster = cluster

    def run_initialization(
        self, hive_uri: str, gcs_key_id: str, gcs_secret: str, duckdb_path: str
    ):
        client = Client(self.cluster)
        self.client = client
        client.register_plugin(
            MetricsWorkerPlugin(
                hive_uri,
                gcs_key_id,
                gcs_secret,
                duckdb_path,
            ),
            name="duckdb-gcs",
        )

    def finalizer(self):
        self.client.close()

    def _ticket_to_query_input(self, ticket: fl.Ticket) -> QueryInput:
        return QueryInput(**json.loads(ticket.ticket))

    def do_get(self, context: fl.ServerCallContext, ticket: fl.Ticket):
        input = self._ticket_to_query_input(ticket)

        runner = MetricsRunner.from_engine_adapter(
            FakeEngineAdapter("duckdb"),
            input.query_str,
            input.ref,
            input.locals,
        )
        # columns = input.to_column_names()

        # def gen():
        #     futures: t.List[concurrent.futures.Future[pd.DataFrame]] = []
        #     for rendered_query in runner.render_rolling_queries(input.start, input.end):
        #         future = asyncio.run_coroutine_threadsafe(
        #             async_gen_batch(self.engine, rendered_query, columns),
        #             self.loop_loop,
        #         )
        #         futures.append(future)
        #     for res in concurrent.futures.as_completed(futures):
        #         yield pa.RecordBatch.from_pandas(res.result())

        def gen_with_dask():
            client = self.client
            futures: t.List[Future] = []
            for rendered_query in runner.render_rolling_queries(input.start, input.end):
                future = client.submit(
                    execute_duckdb_load, rendered_query, input.dependent_tables_map
                )
                # future = asyncio.run_coroutine_threadsafe(
                #     async_gen_batch(self.engine, rendered_query, columns),
                #     self.loop_loop,
                # )
                futures.append(future)
            for res in as_completed(futures):
                yield pa.RecordBatch.from_pandas(res.result())

        logger.debug(
            f"Distributing query for {input.start} to {input.end}: {input.query_str}"
        )
        try:
            return fl.GeneratorStream(
                input.to_arrow_schema(),
                gen_with_dask(),
            )
        except Exception as e:
            logger.error("Caught error generating stream", exc_info=e)
            raise e


def get():
    client = fl.connect("grpc://0.0.0.0:8815")
    input = QueryInput(
        query_str="""
        SELECT bucket_day, to_artifact_id, from_artifact_id, event_source, event_type, SUM(amount) as amount
        FROM metrics.events_daily_to_artifact 
        where bucket_day >= DATE_PARSE(@start_ds, '%Y-%m-%d') and bucket_day < DATE_PARSE(@end_ds, '%Y-%m-%d')
        group by
            bucket_day,
            to_artifact_id,
            from_artifact_id,
            event_source,
            event_type
        """,
        start=datetime.strptime("2024-01-01", "%Y-%m-%d"),
        end=datetime.strptime("2024-01-31", "%Y-%m-%d"),
        dialect="trino",
        columns=[
            ("bucket_day", "VARCHAR"),
            ("to_artifact_id", "VARCHAR"),
            ("from_artifact_id", "VARCHAR"),
            ("event_source", "VARCHAR"),
            ("event_type", "VARCHAR"),
            ("amount", "NUMERIC"),
        ],
        ref=PeerMetricDependencyRef(
            name="", entity_type="artifact", window=30, unit="day"
        ),
        locals={},
        dependent_tables_map={
            "metrics.events_daily_to_artifact": "sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958"
        },
    )
    reader = client.do_get(input.to_ticket())
    r = reader.to_reader()
    for batch in r:
        print(batch.num_rows)


@click.command()
@click.option("--host", envvar="SQLMESH_TRINO_HOST", required=True)
@click.option("--port", default=8080, type=click.INT)
@click.option("--catalog", default="metrics")
@click.option("--user", default="sqlmesh")
@click.option("--gcs-key-id", envvar="METRICS_FLIGHT_SERVER_GCS_KEY_ID", required=True)
@click.option("--gcs-secret", envvar="METRICS_FLIGHT_SERVER_GCS_SECRET", required=True)
@click.option(
    "--worker-duckdb-path",
    envvar="METRICS_FLIGHT_SERVER_WORKER_DUCKDB_PATH",
    required=True,
)
@click.option("--hive-uri", envvar="METRICS_FLIGHT_SERVER_HIVE_URI", required=True)
def main(
    host: str,
    port: int,
    catalog: str,
    user: str,
    gcs_key_id: str,
    gcs_secret: str,
    worker_duckdb_path: str,
    hive_uri: str,
):
    # Start the cluster
    cluster_spec = make_new_cluster(
        "ghcr.io/opensource-observer/dagster-dask:test-1",
        "sqlmesh-flight",
        "sqlmesh-manual",
    )
    cluster = start_duckdb_cluster(
        "sqlmesh-manual",
        gcs_key_id,
        gcs_secret,
        worker_duckdb_path,
        cluster_spec=cluster_spec,
    )

    server = MetricsCalculatorFlightServer(
        cluster,
        TrinoEngine.create(
            host,
            port,
            user,
            catalog,
        ),
    )
    server.run_initialization(hive_uri, gcs_key_id, gcs_secret, worker_duckdb_path)
    with server as s:
        s.serve()


def make_new_cluster(image: str, cluster_id: str, service_account_name: str):
    spec = make_cluster_spec(
        name=f"flight-{cluster_id}",
        resources={
            "requests": {"memory": "1536Mi"},
            "limits": {"memory": "3072Mi"},
        },
        image=image,
    )
    spec["spec"]["worker"]["spec"]["tolerations"] = [
        {
            "key": "pool_type",
            "effect": "NoSchedule",
            "operator": "Equal",
            "value": "sqlmesh-worker",
        }
    ]
    spec["spec"]["worker"]["spec"]["nodeSelector"] = {"pool_type": "sqlmesh-worker"}

    # Give the workers a different resource allocation
    for container in spec["spec"]["worker"]["spec"]["containers"]:
        container["resources"] = {
            "limits": {
                "memory": "200000Mi",
            },
            "requests": {
                "memory": "150000Mi",
            },
        }
        volume_mounts = container.get("volumeMounts", [])
        volume_mounts.append(
            {
                "mountPath": "/scratch",
                "name": "scratch",
            }
        )
        if container["name"] == "worker":
            args: t.List[str] = container["args"]
            args.append("--nthreads")
            args.append("1")
            args.append("--nworkers")
            args.append("1")
            args.append("--memory-limit")
            args.append("0")
        container["volumeMounts"] = volume_mounts
    volumes = spec["spec"]["worker"]["spec"].get("volumes", [])
    volumes.append(
        {
            "name": "scratch",
            "emptyDir": {},
        }
    )
    spec["spec"]["worker"]["spec"]["volumes"] = volumes
    spec["spec"]["worker"]["spec"]["serviceAccountName"] = service_account_name

    return spec


if __name__ == "__main__":
    main()
