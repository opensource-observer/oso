"""A python arrow service that is used to as a proxy to the cluster of compute for the
metrics tools. This allows us to change the underlying compute infrastructure
while maintaining the same interface to the sqlmesh runner.
"""

import concurrent.futures
import logging
import sys
import typing as t
import json
import click
import time
import concurrent
from metrics_tools.compute.cluster import start_duckdb_cluster
from metrics_tools.compute.worker import MetricsWorkerPlugin
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.runner import FakeEngineAdapter, MetricsRunner
from metrics_tools.transformer.tables import MapTableTransform
from metrics_tools.transformer.transformer import SQLTransformer
import pyarrow as pa
import pyarrow.flight as fl
import asyncio
import pandas as pd
import threading
import trino
import queue
from sqlglot import exp
from sqlmesh.core.dialect import parse_one
from trino.dbapi import Connection, Cursor
import abc
import uuid
from pydantic import BaseModel
from datetime import datetime
from dask.distributed import Client, get_worker, Future, as_completed, print as dprint
from dask_kubernetes.operator import KubeCluster, make_cluster_spec
from dask_kubernetes.operator.kubecluster.kubecluster import CreateMode
from dataclasses import dataclass


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
    "TIMESTAMP": pa.timestamp("us"),
}


class QueryInput(BaseModel):
    query_str: str
    start: datetime
    end: datetime
    dialect: str
    batch_size: int
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
    def run_query(self, query: str) -> Cursor:
        raise NotImplementedError("run_query not implemented")


class TrinoEngine(Engine):
    @classmethod
    def create(cls, host: str, port: int, user: str, catalog: str):
        conn = trino.dbapi.connect(
            host=host,
            port=port,
            user=user,
            catalog=catalog,
        )
        return cls(conn)

    def __init__(self, conn: Connection):
        self._conn = conn

    def run_query(self, query: str) -> Cursor:
        cursor = self._conn.cursor()
        logger.info(f"EXECUTING: {query}")
        return cursor.execute(query)


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def run_coroutine_in_thread(coro):
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=start_loop, args=(loop,))
    thread.start()


def execute_duckdb_load(id: int, queries: t.List[str], dependencies: t.Dict[str, str]):
    dprint("Starting duckdb load")
    worker = get_worker()
    plugin = t.cast(MetricsWorkerPlugin, worker.plugins["duckdb-gcs"])
    for ref, actual in dependencies.items():
        dprint(f"Loading cache for {ref}:{actual}")
        plugin.get_for_cache(ref, actual)
    conn = plugin.connection
    results: t.List[pd.DataFrame] = []
    for query in queries:
        result = conn.execute(query).df()
        results.append(result)

    return DuckdbLoadedItem(
        id=id,
        df=pd.concat(results, ignore_index=True, sort=False),
    )


@dataclass(kw_only=True)
class DuckdbLoadedItem:
    id: int
    df: pd.DataFrame


@dataclass(kw_only=True)
class ResultQueueItem:
    id: int
    record_batch: pa.RecordBatch


class MetricsCalculatorFlightServer(fl.FlightServerBase):
    def __init__(
        self,
        cluster: KubeCluster,
        engine: TrinoEngine,
        gcs_bucket: str,
        location: str = "grpc://0.0.0.0:8815",
        exported_map: t.Optional[t.Dict[str, str]] = None,
        downloaders: int = 64,
        queue_size: int = 100,
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
        self.exported_map: t.Dict[str, str] = exported_map or {}
        self.gcs_bucket = gcs_bucket
        self.queue_size = queue_size
        self.downloader_count = downloaders

    def run_initialization(
        self, hive_uri: str, gcs_key_id: str, gcs_secret: str, duckdb_path: str
    ):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        client = Client(self.cluster)
        self.client = client
        client.register_plugin(
            MetricsWorkerPlugin(
                self.gcs_bucket,
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

    def table_rewrite(self, query: str, rewrite_map: t.Dict[str, str]):
        transformer = SQLTransformer(
            transforms=[
                MapTableTransform(rewrite_map),
            ]
        )
        return transformer.transform(query)

    def export_table_for_cache(self, table: str):
        # Using the actual name
        # Export with trino
        if table in self.exported_map:
            logger.debug(f"CACHE HIT FOR {table}")
            return self.exported_map[table]

        columns: t.List[t.Tuple[str, str]] = []

        col_result = self.engine.run_query(f"SHOW COLUMNS FROM {table}").fetchall()
        for row in col_result:
            column_name = row[0]
            column_type = row[1]
            columns.append((column_name, column_type))

        table_exp = exp.to_table(table)
        logger.info(f"RETREIVED COLUMNS: {columns}")
        export_table_name = f"export_{table_exp.this.this}_{uuid.uuid4().hex}"

        base_create_query = f"""
            CREATE table "source"."export"."{export_table_name}" (
                placeholder VARCHAR,
            ) WITH (
                format = 'PARQUET',
                external_location = 'gs://{self.gcs_bucket}/trino-export/{export_table_name}/'
            )
        """
        create_query = parse_one(base_create_query)
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(
                    this=exp.to_identifier(column_name),
                    kind=parse_one(column_type, into=exp.DataType),
                )
                for column_name, column_type in columns
            ],
        )

        self.engine.run_query(create_query.sql(dialect="trino"))

        base_insert_query = f"""
            INSERT INTO "source"."export"."{export_table_name}" (placeholder)
            SELECT placeholder
            FROM {table_exp}
        """

        column_identifiers = [
            exp.to_identifier(column_name) for column_name, _ in columns
        ]

        insert_query = parse_one(base_insert_query)
        insert_query.this.set(
            "expressions",
            column_identifiers,
        )
        select = t.cast(exp.Select, insert_query.expression)
        select.set("expressions", column_identifiers)

        self.engine.run_query(insert_query.sql(dialect="trino"))

        self.exported_map[table] = export_table_name
        return self.exported_map[table]

    # def shutdown(self):
    #     pass

    def do_get(self, context: fl.ServerCallContext, ticket: fl.Ticket):
        input = self._ticket_to_query_input(ticket)

        exported_dependent_tables_map: t.Dict[str, str] = {}

        # Parse the query
        for ref_name, actual_name in input.dependent_tables_map.items():
            # Any deps, use trino to export to gcs
            exported_table_name = self.export_table_for_cache(actual_name)
            exported_dependent_tables_map[ref_name] = exported_table_name

        # rewrite the query for the temporary caches made by trino
        # ex = self.table_rewrite(input.query_str, exported_dependent_tables_map)
        # if len(ex) != 1:
        #     raise Exception("unexpected number of expressions")

        rewritten_query = parse_one(input.query_str).sql(dialect="duckdb")
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

        def gen_with_dask(
            rewritten_query: str,
            input: QueryInput,
            exported_dependent_tables_map: t.Dict[str, str],
            download_queue: queue.Queue[Future],
        ):
            client = self.client
            futures: t.List[Future] = []
            current_batch: t.List[str] = []
            task_ids: t.List[int] = []

            runner = MetricsRunner.from_engine_adapter(
                FakeEngineAdapter("duckdb"),
                rewritten_query,
                input.ref,
                input.locals,
            )

            task_id = 0
            for rendered_query in runner.render_rolling_queries(input.start, input.end):
                current_batch.append(rendered_query)
                if len(current_batch) >= input.batch_size:
                    future = client.submit(
                        execute_duckdb_load,
                        task_id,
                        current_batch[:],
                        exported_dependent_tables_map,
                    )
                    futures.append(future)
                    current_batch = []
                    task_ids.append(task_id)
                    task_id += 1
            if len(current_batch) > 0:
                future = client.submit(
                    execute_duckdb_load,
                    task_id,
                    current_batch[:],
                    exported_dependent_tables_map,
                )
                futures.append(future)
                task_ids.append(task_id)
                task_id += 1

            completed_batches = 0
            total_batches = len(futures)
            for future in as_completed(futures):
                completed_batches += 1
                logger.info(f"progress received [{completed_batches}/{total_batches}]")
                future = t.cast(Future, future)
                if future.cancelled:
                    if future.done():
                        logger.info("future actually done???")
                    else:
                        logger.error("future cancelled. skipping for now?")
                        print(future)
                        print(future.result() is not None)
                        continue
                download_queue.put(future)
            return task_ids

        def downloader(
            kill_event: threading.Event,
            download_queue: queue.Queue[Future],
            res_queue: queue.Queue[ResultQueueItem],
        ):
            logger.debug("waiting for download")
            while True:
                try:
                    future = download_queue.get(timeout=0.1)
                    try:
                        item = t.cast(DuckdbLoadedItem, future.result())
                        record_batch = pa.RecordBatch.from_pandas(item.df)
                        res_queue.put(
                            ResultQueueItem(
                                id=item.id,
                                record_batch=record_batch,
                            )
                        )
                        logger.debug("download completed")
                    finally:
                        download_queue.task_done()
                except queue.Empty:
                    if kill_event.is_set():
                        logger.debug("shutting down downloader")
                        return
                if kill_event.is_set() and not download_queue.empty():
                    logger.debug("shutting down downloader prematurely")
                    return

        def gen_record_batches(size: int):
            download_queue: queue.Queue[Future] = queue.Queue(maxsize=size)
            res_queue: queue.Queue[ResultQueueItem] = queue.Queue(maxsize=size)
            kill_event = threading.Event()
            result_queue_timeout = 5.0
            max_result_timeout = 300

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.downloader_count + 5
            ) as executor:
                dask_thread = executor.submit(
                    gen_with_dask,
                    rewritten_query,
                    input,
                    exported_dependent_tables_map,
                    download_queue,
                )
                downloaders = []
                for i in range(self.downloader_count):
                    downloaders.append(
                        executor.submit(
                            downloader, kill_event, download_queue, res_queue
                        )
                    )

                wait_retries = 0

                completed_task_ids: t.Set[int] = set()
                task_ids: t.Optional[t.Set[int]] = None

                while task_ids != completed_task_ids:
                    try:
                        result = res_queue.get(timeout=result_queue_timeout)
                        wait_retries = 0
                        logger.debug("sending batch to client")

                        completed_task_ids.add(result.id)

                        yield result.record_batch
                    except queue.Empty:
                        wait_retries += 1
                    if task_ids is None:
                        # If the dask thread is done we know if we can check for completion
                        if dask_thread.done():
                            task_ids = set(dask_thread.result())
                    else:
                        # If we have waited longer then 15 mins let's stop waiting
                        current_wait_time = wait_retries * result_queue_timeout
                        if current_wait_time > max_result_timeout:
                            logger.debug(
                                "record batches might be completed. with some kind of error"
                            )
                            break
                kill_event.set()
                logger.debug("waiting for the downloaders to shutdown")
                executor.shutdown(cancel_futures=True)

        logger.debug(
            f"Distributing query for {input.start} to {input.end}: {rewritten_query}"
        )
        try:
            return fl.GeneratorStream(
                input.to_arrow_schema(),
                gen_record_batches(size=self.queue_size),
            )
        except Exception as e:
            print("caught error")
            logger.error("Caught error generating stream", exc_info=e)
            raise e


def run_get(
    start: str,
    end: str,
    batch_size: int = 1,
):
    run_start = time.time()
    client = fl.connect("grpc://0.0.0.0:8815")
    input = QueryInput(
        query_str="""
        SELECT bucket_day, to_artifact_id, from_artifact_id, event_source, event_type, SUM(amount) as amount
        FROM metrics.events_daily_to_artifact 
        where bucket_day >= strptime(@start_ds, '%Y-%m-%d') and bucket_day <= strptime(@end_ds, '%Y-%m-%d')
        group by
            bucket_day,
            to_artifact_id,
            from_artifact_id,
            event_source,
            event_type
        """,
        start=datetime.strptime(start, "%Y-%m-%d"),
        end=datetime.strptime(end, "%Y-%m-%d"),
        dialect="duckdb",
        columns=[
            ("bucket_day", "TIMESTAMP"),
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
        batch_size=batch_size,
    )
    reader = client.do_get(input.to_ticket())
    r = reader.to_reader()
    count = 0
    for batch in r:
        count += 1
        print(f"[{count}] ROWS={batch.num_rows}")
    run_end = time.time()
    print(f"DURATION={run_end - run_start}s")


@click.command()
@click.option("--host", envvar="SQLMESH_TRINO_HOST", required=True)
@click.option("--port", default=8080, type=click.INT)
@click.option("--catalog", default="metrics")
@click.option("--user", default="sqlmesh")
@click.option("--gcs-bucket", envvar="METRICS_FLIGHT_SERVER_GCS_BUCKET", required=True)
@click.option("--gcs-key-id", envvar="METRICS_FLIGHT_SERVER_GCS_KEY_ID", required=True)
@click.option("--gcs-secret", envvar="METRICS_FLIGHT_SERVER_GCS_SECRET", required=True)
@click.option(
    "--worker-duckdb-path",
    envvar="METRICS_FLIGHT_SERVER_WORKER_DUCKDB_PATH",
    required=True,
)
@click.option("--hive-uri", envvar="METRICS_FLIGHT_SERVER_HIVE_URI", required=True)
@click.option("--image-tag", required=True)
@click.option("--threads", type=click.INT, default=16)
@click.option("--worker-memory-limit", default="90000Mi")
@click.option("--worker-memory-request", default="75000Mi")
@click.option("--scheduler-memory-limit", default="90000Mi")
@click.option("--scheduler-memory-request", default="75000Mi")
@click.option("--cluster-only/--no-cluster-only", default=False)
@click.option("--cluster-name", default="sqlmesh-flight")
@click.option("--cluster-namespace", default="sqlmesh-manual")
def main(
    host: str,
    port: int,
    catalog: str,
    user: str,
    gcs_bucket: str,
    gcs_key_id: str,
    gcs_secret: str,
    worker_duckdb_path: str,
    hive_uri: str,
    image_tag: str,
    threads: int,
    scheduler_memory_limit: str,
    scheduler_memory_request: str,
    worker_memory_limit: str,
    worker_memory_request: str,
    cluster_only: bool,
    cluster_name: str,
    cluster_namespace: str,
):
    cluster_spec = make_new_cluster(
        f"ghcr.io/opensource-observer/dagster-dask:{image_tag}",
        cluster_name,
        cluster_namespace,
        threads=threads,
        scheduler_memory_limit=scheduler_memory_limit,
        scheduler_memory_request=scheduler_memory_request,
        worker_memory_limit=worker_memory_limit,
        worker_memory_request=worker_memory_request,
    )

    if cluster_only:
        # Start the cluster
        cluster = start_duckdb_cluster(
            cluster_namespace,
            gcs_key_id,
            gcs_secret,
            worker_duckdb_path,
            cluster_spec=cluster_spec,
        )
        try:
            while True:
                time.sleep(1.0)
        finally:
            cluster.close()
    else:
        cluster = KubeCluster(
            name=cluster_name,
            namespace=cluster_namespace,
            create_mode=CreateMode.CONNECT_ONLY,
            shutdown_on_close=False,
        )
        server = MetricsCalculatorFlightServer(
            cluster,
            TrinoEngine.create(
                host,
                port,
                user,
                catalog,
            ),
            gcs_bucket,
            exported_map={
                "sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958": "export_metrics__events_daily_to_artifact__2357434958_5def5e890a984cf99f7364ce3c2bb958",
            },
        )
        server.run_initialization(hive_uri, gcs_key_id, gcs_secret, worker_duckdb_path)
        with server as s:
            s.serve()


def make_new_cluster(
    image: str,
    cluster_id: str,
    service_account_name: str,
    threads: int,
    scheduler_memory_request: str,
    scheduler_memory_limit: str,
    worker_memory_request: str,
    worker_memory_limit: str,
):
    spec = make_cluster_spec(
        name=f"{cluster_id}",
        resources={
            "requests": {"memory": scheduler_memory_request},
            "limits": {"memory": scheduler_memory_limit},
        },
        image=image,
    )
    spec["spec"]["scheduler"]["spec"]["tolerations"] = [
        {
            "key": "pool_type",
            "effect": "NoSchedule",
            "operator": "Equal",
            "value": "sqlmesh-worker",
        }
    ]
    spec["spec"]["scheduler"]["spec"]["nodeSelector"] = {"pool_type": "sqlmesh-worker"}

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
                "memory": worker_memory_limit,
            },
            "requests": {
                "memory": worker_memory_request,
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
            args.append(f"{threads}")
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
