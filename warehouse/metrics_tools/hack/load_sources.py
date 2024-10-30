import typing as t
import os
import click
import duckdb
from google.cloud import bigquery, storage
from oso_dagster.utils.bq import export_to_gcs, BigQueryTableConfig


def download_parquet_files_from_gcs(
    gcs_client: storage.Client,
    bucket_name: str,
    prefix: str,
    local_folder: str,
):
    bucket = gcs_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    for blob in blobs:
        if blob.name.endswith(".parquet"):
            local_file_path = os.path.join(local_folder, os.path.basename(blob.name))
            blob.download_to_filename(local_file_path)
            print(f"Downloaded {blob.name} to {local_file_path}")


def load_parquet_to_duckdb(
    con: duckdb.DuckDBPyConnection, parquet_folder: str, table_name: str
):
    parquet_files = [f for f in os.listdir(parquet_folder) if f.endswith(".parquet")]

    table_exists = False
    for parquet_file in parquet_files:
        file_path = os.path.join(parquet_folder, parquet_file)

        if table_exists:
            # If table exists, append the data
            con.execute(
                f"INSERT INTO {table_name} SELECT * FROM read_parquet('{file_path}');"
            )
            print(f"Appended {parquet_file} to DuckDB table {table_name}")
        else:
            # If table does not exist, create it with the Parquet data
            con.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}');"
            )
            print(f"Loaded {parquet_file} into new DuckDB table {table_name}")
            table_exists = True

    con.close()


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

    def run(self, tables: t.List[str]):
        self._db_conn.execute("CREATE SCHEMA IF NOT EXISTS sources;")
        for table in tables:
            self._export_and_load(table)

    def make_download_path(self, table_name: str):
        return os.path.join(self._download_path, self._version, table_name)

    def _export_and_load(self, table: str):
        events_gcs_path = os.path.join(
            self.gcs_path,
            self._version,
            "timeseries_events_by_artifact_v0",
        )
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

        download_path = self.make_download_path(table)

        # Download the gcs stuff to a local working directory
        prefix = os.path.join(self._gcs_bucket_path, self._version)
        download_parquet_files_from_gcs(
            self._gcs_client,
            self._gcs_bucket_name,
            prefix,
            download_path,
        )

        # Load the data into duckdb
        load_parquet_to_duckdb(
            self._db_conn,
            download_path,
            f"sources.{table}",
        )

        # Delete the downloaded files
        os.rmdir(download_path)


@click.command()
@click.option("--db-path", envvar="DB_PATH", required=True)
@click.option("--gcs-bucket-name", envvar="GCS_BUCKET", required=True)
@click.option("--gcs-bucket-path", envvar="GCS_BUCKET_PATH", required=True)
@click.option("--download-path", envvar="DOWNLOAD_PATH", required=True)
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
        ]
    )


if __name__ == "__main__":
    main()
