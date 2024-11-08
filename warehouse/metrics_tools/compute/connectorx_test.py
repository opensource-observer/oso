import os
import connectorx as cx
import duckdb


def main():
    conn = duckdb.connect("/scratch/worker.db")
    conn.sql("CREATE SCHEMA IF NOT EXISTS metrics")

    trino_uri = f"trino+http://sqlmesh@{os.environ['SQLMESH_TRINO_HOST']}:8080/metrics"
    res = cx.read_sql(  # noqa: F841
        trino_uri,
        "SELECT * FROM sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958",
        return_type="arrow",
        partition_on="bucket_day",
        partition_num=100,
    )
    conn.sql(
        """
    CREATE TABLE IF NOT EXISTS metrics.events_daily_to_artifact AS
    SELECT * FROM res
    """
    )


if __name__ == "__main__":
    main()
