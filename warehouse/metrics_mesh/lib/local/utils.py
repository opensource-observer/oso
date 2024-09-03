import typing as t
import duckdb
from google.cloud import bigquery


def bq_to_duckdb(table_mapping: t.Dict[str, str], duckdb_path: str):
    """Copies the tables in table_mapping to tables in duckdb

    The table_mapping is in the form { "bigquery_table_fqn": "duckdb_table_fqn" }
    """
    bqclient = bigquery.Client()
    conn = duckdb.connect(duckdb_path)

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


def initialize_local_duckdb():
    import os
    import dotenv

    dotenv.load_dotenv()

    bq_to_duckdb(
        {
            # We need to rename this once we run the oso_playground dbt again
            "opensource-observer.oso_playground.int_events": "sources.timeseries_events_by_artifact_v0",
            "opensource-observer.oso_playground.artifacts_by_project_v1": "sources.artifacts_by_project_v1",
        },
        os.environ["SQLMESH_DUCKDB_LOCAL_PATH"],
    )


if __name__ == "__main__":
    initialize_local_duckdb()
