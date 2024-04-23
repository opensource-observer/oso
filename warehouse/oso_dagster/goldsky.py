from typing import List, Optional
import uuid
import duckdb
from dagster import DagsterLogManager


class GoldskyDuckDB:
    @staticmethod
    def connect(
        cls,
        destination_path: str,
        bucket_name: str,
        key_id: str,
        secret: str,
        path: str,
        log: DagsterLogManager,
    ):
        conn = duckdb.connect(path)
        conn.sql(
            f"""
        CREATE SECRET (
            TYPE GCS,
            KEY_ID '{key_id}',
            SECRET '{secret}'
        );
        """
        )
        return cls(bucket_name, destination_path, log, conn)

    def __init__(
        self,
        bucket_name: str,
        destination_path: str,
        log: DagsterLogManager,
        conn: duckdb.DuckDBPyConnection,
    ):
        self.destination_path = destination_path
        self.bucket_name = bucket_name
        self.conn = conn
        self.log = log

    def full_dest_table_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/table_{batch_id}.parquet"

    def full_dest_delete_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/delete_{batch_id}.parquet"

    def full_dest_deduped_path(self, worker: str, batch_id: int):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/deduped_{batch_id}.parquet"

    def wildcard_deduped_path(self, worker: str):
        return f"gs://{self.bucket_name}/{self.destination_path}/{worker}/deduped_*.parquet"

    def remove_dupes(self, worker: str, batches: List[int]):
        conn = self.conn
        bucket_name = self.bucket_name

        base = f"gs://{bucket_name}"

    def remove_dupe_for_batch(self, worker: str, batch_id: int):
        self.conn.sql(
            f"""
        CREATE TABLE deduped_{batch_id}
        AS
        SELECT * FROM read_parquet('{self.full_dest_table_path(worker, batch_id)}')
        """
        )

        self.conn.sql(
            f""" 
        DELETE FROM deduped_{batch_id}
        WHERE id in (
            SELECT id FROM read_parquest('{self.full_dest_delete_path(worker, batch_id)}')
        )
        """
        )

        self.conn.sql(
            f"""
        COPY deduped_{batch_id} TO '{self.full_dest_deduped_path(worker, batch_id)}';
        """
        )

    def load_and_merge(self, worker: str, batch_id: int, blob_names: List[str]):
        conn = self.conn
        bucket_name = self.bucket_name

        base = f"gs://{bucket_name}/"

        size = len(blob_names)

        for i in range(size):
            self.log.debug(f"Blob {blob_names[i]}")
            file_ref = f"{base}/{blob_names[i]}"
            conn.sql(
                f"""
            CREATE OR REPLACE VIEW checkpoint_{batch_id}_{i}
            AS
            SELECT *
            FROM read_parquet('{file_ref}');
            """
            )

        merged_table = f"merged_{batch_id}"
        try:
            conn.sql(
                f"""
            CREATE TABLE {merged_table}
            AS
            SELECT *
            FROM checkpoint_{batch_id}_{i}
            """
            )
        except duckdb.CatalogException:
            conn.sql(f"DROP TABLE {merged_table};")
            conn.sql(
                f"""
            CREATE TABLE {merged_table}
            AS
            SELECT *
            FROM checkpoint_{batch_id}_0
            """
            )

        for i in range(size - 1):
            self.log.debug(f"Merging {blob_names[i+1]}")
            checkpoint_table = f"checkpoint_{batch_id}_{i+1}"
            rows = conn.sql(
                f"""
            SELECT *
            FROM {merged_table} AS m
            INNER JOIN {checkpoint_table} as ch
            ON m.id = ch.id;
            """
            )
            if len(rows) > 0:
                conn.sql(
                    f"""
                DELETE FROM {merged_table} WHERE id IN (
                    SELECT m.id
                    FROM merged AS m
                    INNER JOIN {checkpoint_table} AS ch
                    ON m.id = ch.id
                );
                """
                )
            conn.sql(
                f"""
            INSERT INTO {merged_table}
            SELECT * FROM {checkpoint_table};
            """
            )
        conn.sql(
            f"""
        COPY {merged_table} TO '{self.full_dest_table_path(worker, batch_id)}';
        """
        )
        # Create a table to store the ids for this
        conn.sql(
            f"""
        CREATE TABLE merged_ids_{batch_id}
        AS
        SELECT id as "id" FROM {merged_table}
        """
        )

        if batch_id > 0:
            prev_batch_id = batch_id - 1
            # Check for any intersections with the last table. We need to create a "delete patch"
            conn.sql(
                f"""
            CREATE TABLE delete_patch_{prev_batch_id}
            AS
            SELECT pmi.id 
            FROM merged_ids_{prev_batch_id} AS pmi
            INNER JOIN {merged_table} AS m
                ON m.id = pmi.id;
            """
            )
            conn.sql(
                f"""
            DROP TABLE merged_ids_{prev_batch_id};
            """
            )
            conn.sql(
                f"""
            COPY delete_patch_{prev_batch_id} TO '{self.full_dest_delete_path(worker, prev_batch_id)}';
            """
            )
            conn.sql(
                f"""
            DROP TABLE delete_patch_{prev_batch_id};
            """
            )
        conn.sql(
            f"""
        DROP TABLE {merged_table};
        """
        )


def load_and_merge(
    log: DagsterLogManager,
    conn: duckdb.DuckDBPyConnection,
    bucket_name: str,
    blob_names: List[str],
    batch_id: int,
    key_id: str,
    secret: str,
    destination_path: str,
):
    conn.sql(
        f"""
    CREATE SECRET (
        TYPE GCS,
        KEY_ID '{key_id}',
        SECRET '{secret}'
    );
    """
    )

    base = f"gs://{bucket_name}/"

    size = len(blob_names)

    for i in range(size):
        log.debug(f"Blob {blob_names[i]}")
        file_ref = f"{base}/{blob_names[i]}"
        conn.sql(
            f"""
        CREATE OR REPLACE VIEW checkpoint_{batch_id}_{i}
        AS
        SELECT *
        FROM read_parquet('{file_ref}');
        """
        )

    merged_table = f"merged_{batch_id}"
    try:
        conn.sql(
            f"""
        CREATE TABLE {merged_table}
        AS
        SELECT *
        FROM checkpoint_{batch_id}_{i}
        """
        )
    except duckdb.CatalogException:
        conn.sql(f"DROP TABLE {merged_table};")
        conn.sql(
            f"""
        CREATE TABLE {merged_table}
        AS
        SELECT *
        FROM checkpoint_{batch_id}_0
        """
        )

    for i in range(size - 1):
        log.debug(f"Merging {blob_names[i+1]}")
        checkpoint_table = f"checkpoint_{batch_id}_{i+1}"
        rows = conn.sql(
            f"""
        SELECT *
        FROM {merged_table} AS m
        INNER JOIN {checkpoint_table} as ch
          ON m.id = ch.id;
        """
        )
        if len(rows) > 0:
            conn.sql(
                f"""
            DELETE FROM {merged_table} WHERE id in (
                SELECT m.id
                FROM merged AS m
                INNER JOIN {checkpoint_table} AS ch
                  ON m.id = ch.id
            );
            """
            )
        conn.sql(
            f"""
        INSERT INTO {merged_table}
        SELECT * FROM {checkpoint_table};
        """
        )
    conn.sql(
        f"""
    COPY {merged_table} TO 'gs://{bucket_name}/{destination_path}/table_{batch_id}.parquet';
    """
    )
    # Create a table to store the ids for this
    conn.sql(
        f"""
    CREATE TABLE merged_ids_{batch_id}
    AS
    SELECT id as "id" FROM {merged_table}
    """
    )

    if batch_id > 0:
        prev_batch_id = batch_id - 1
        # Check for any intersections with the last table. We need to create a "delete patch"
        conn.sql(
            f"""
        CREATE TABLE delete_patch_{prev_batch_id}
        AS
        SELECT pmi.id 
        FROM merged_ids_{prev_batch_id} AS pmi
        INNER JOIN {merged_table} AS m
            ON m.id = pmi.id;
        """
        )
        conn.sql(
            f"""
        DROP TABLE merged_ids_{prev_batch_id};
        """
        )
        conn.sql(
            f"""
        COPY delete_patch_{prev_batch_id} TO 'gs://{bucket_name}/{destination_path}/delete_{prev_batch_id}.parquet';
        """
        )
        conn.sql(
            f"""
        DROP TABLE delete_patch_{prev_batch_id};
        """
        )
    conn.sql(
        f"""
    DROP TABLE {merged_table};
    """
    )
