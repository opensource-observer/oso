import typing as t
import os
import click
import duckdb
import queue
import concurrent.futures
from dataclasses import dataclass
from boltons import fileutils
from google.cloud import bigquery, storage
from oso_dagster.utils.bq import export_to_gcs, BigQueryTableConfig


@dataclass(kw_only=True)
class Work:
    bucket_name: str
    blob_path: str
    destination_path: str
    table_name: str


@dataclass(kw_only=True)
class ParquetLoaded:
    path: str
    table_name: str


class Cancel(Exception):
    pass


class Noop:
    pass


def get_or_cancel[T](queue: queue.Queue, expected_type: t.Type[T]) -> T:
    item = queue.get()
    if isinstance(item, expected_type):
        return t.cast(T, item)
    raise Cancel("cancel queue")


def download_parquet_from_gcs(
    work_queue: queue.Queue,
    result_queue: queue.Queue,
):
    print("starting parquet worker")
    client = storage.Client()
    while True:
        try:
            work = get_or_cancel(work_queue, Work)
        except Cancel:
            break
        print(f"starting download to {work.destination_path}")
        # Download
        with open(work.destination_path, "wb") as file_obj:
            blob_uri = os.path.join("gs://", work.bucket_name, work.blob_path)
            client.download_blob_to_file(
                blob_uri,
                file_obj,
            )
        print(f"downloaded: {blob_uri} to {work.destination_path}")
        result_queue.put(
            ParquetLoaded(
                path=work.destination_path,
                table_name=work.table_name,
            )
        )
        # Enqueue the result
        work_queue.task_done()
    print("download worker done")


def load_into_duckdb(conn: duckdb.DuckDBPyConnection, queue: queue.Queue):
    already_created: t.Dict[str, bool] = {}

    print("starting duckdb worker")
    while True:
        try:
            loaded = get_or_cancel(queue, ParquetLoaded)
        except Cancel:
            break
        print("hi")
        # Load the file into duckdb
        if loaded.table_name not in already_created:
            already_created[loaded.table_name] = True
            conn.execute(
                f"CREATE TABLE {loaded.table_name} AS SELECT * FROM read_parquet('{loaded.path}');"
            )
            print(f"Loaded {loaded.path} into new DuckDB table {loaded.table_name}")
        else:
            conn.execute(
                f"INSERT INTO {loaded.table_name} SELECT * FROM read_parquet('{loaded.path}');"
            )
            print(f"Appended {loaded.path} to DuckDB table {loaded.table_name}")
        # Delete the file
        os.remove(loaded.path)
        queue.task_done()
    print("duckdb done")


def get_parquet_work_list(
    gcs_client: storage.Client,
    bucket_name: str,
    prefix: str,
    local_folder: str,
    table_name: str,
) -> t.List[Work]:
    bucket = gcs_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    work_list: t.List[Work] = []

    for blob in blobs:
        if blob.name.endswith(".parquet"):
            local_file_path = os.path.join(local_folder, os.path.basename(blob.name))
            work = Work(
                bucket_name=bucket_name,
                blob_path=blob.name,
                destination_path=local_file_path,
                table_name=table_name,
            )
            work_list.append(work)
    return work_list


def bq_to_duckdb(table_mapping: t.Dict[str, str], conn: duckdb.DuckDBPyConnection):
    """Copies the tables in table_mapping to tables in duckdb

    The table_mapping is in the form { "bigquery_table_fqn": "duckdb_table_fqn" }
    """
    bqclient = bigquery.Client()

    conn.sql("CREATE SCHEMA IF NOT EXISTS sources;")

    for bq_table, duckdb_table in table_mapping.items():
        table = bigquery.TableReference.from_string(bq_table)
        rows = bqclient.list_rows(table)

        table_as_arrow = rows.to_arrow(create_bqstorage_client=True)  # noqa: F841

        conn.sql(
            f"""
            CREATE TABLE IF NOT EXISTS {duckdb_table} AS 
            SELECT * FROM table_as_arrow
        """
        )


class ExporterLoader:
    def __init__(
        self,
        *,
        bq_client: bigquery.Client,
        gcs_client: storage.Client,
        duckdb_conn: duckdb.DuckDBPyConnection,
        version: str,
        gcs_bucket_name: str,
        gcs_bucket_path: str,
        download_path: str,
    ):
        self._bq_client = bq_client
        self._gcs_client = gcs_client
        self._version = version
        self._gcs_bucket_name = gcs_bucket_name
        self._gcs_bucket_path = gcs_bucket_path
        self._download_path = download_path
        self._db_conn = duckdb_conn

    @property
    def gcs_path(self):
        return os.path.join("gs://", self._gcs_bucket_name, self._gcs_bucket_path)

    def run(self, tables: t.List[str], resume: bool = False):
        self._db_conn.execute("CREATE SCHEMA IF NOT EXISTS sources;")

        work_queue = queue.Queue()
        result_queue = queue.Queue()
        workers = 12

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # Make 8 workers for downloads and one for duckdb
            all_futures: t.List[concurrent.futures.Future] = []
            for _ in range(workers - 1):
                all_futures.append(
                    executor.submit(download_parquet_from_gcs, work_queue, result_queue)
                )
            all_futures.append(
                executor.submit(load_into_duckdb, self._db_conn, result_queue)
            )

            for table in tables:
                print(f"loading work for {table}")
                work_list = self._export_and_load(table, resume)
                for work in work_list:
                    work_queue.put(work)

            for _ in range(workers - 1):
                work_queue.put(Noop())

            work_queue.join()
            result_queue.put(Noop())

            concurrent.futures.wait(all_futures)

    def make_download_path(self, table_name: str):
        download_path = os.path.join(self._download_path, self._version, table_name)
        fileutils.mkdir_p(download_path)
        return download_path

    def _export_and_load(self, table: str, resume: bool = False):
        events_gcs_path = os.path.join(
            self.gcs_path,
            self._version,
            table,
        )
        if not resume:
            export_to_gcs(
                self._bq_client,
                BigQueryTableConfig(
                    project_id="opensource-observer",
                    dataset_name="oso",
                    service_account=None,
                    table_name=table,
                ),
                gcs_path=events_gcs_path,
            )
            print("gcs exported")

        download_path = self.make_download_path(table)

        # Download the gcs stuff to a local working directory
        prefix = os.path.join(self._gcs_bucket_path, self._version)

        print("getting list of work")
        # Load the data into duckdb
        return get_parquet_work_list(
            self._gcs_client, self._gcs_bucket_name, prefix, download_path, table
        )


@click.command()
@click.option("--db-path", envvar="DB_PATH", required=True)
@click.option("--gcs-bucket-name", envvar="GCS_BUCKET", required=True)
@click.option("--gcs-bucket-path", envvar="GCS_BUCKET_PATH", required=True)
@click.option("--download-path", envvar="DOWNLOAD_PATH", required=True)
@click.option("--resume/--no-resume", default=False)
@click.option(
    "--version",
    envvar="VERSION",
    required=True,
    help="arbitrary version number for handling retries",
)
def main(
    db_path: str,
    gcs_bucket_name: str,
    gcs_bucket_path: str,
    download_path: str,
    resume: bool,
    version: str,
):
    duckdb_conn = duckdb.connect(db_path)

    bq_client = bigquery.Client()
    gcs_client = storage.Client()

    exlo = ExporterLoader(
        bq_client=bq_client,
        gcs_client=gcs_client,
        duckdb_conn=duckdb_conn,
        gcs_bucket_name=gcs_bucket_name,
        gcs_bucket_path=gcs_bucket_path,
        download_path=download_path,
        version=version,
    )
    exlo.run(
        [
            "timeseries_events_by_artifact_v0",
            "artifacts_by_project_v1",
            "projects_by_collection_v1",
        ],
        resume=resume,
    )


if __name__ == "__main__":
    main()
