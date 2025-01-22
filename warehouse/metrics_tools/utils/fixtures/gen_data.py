import base64
import hashlib
import os
import typing as t
from datetime import datetime

import arrow
import duckdb
import pandas as pd

METRICS_TOOLS_DB_FIXTURE_PATH = os.environ.get("METRICS_TOOLS_DB_FIXTURE_PATH", "")


class MetricsDBFixture:
    @classmethod
    def create(cls, encode_ids: bool = False):
        database_path = ":memory:"
        if METRICS_TOOLS_DB_FIXTURE_PATH:
            database_path = os.path.join(
                METRICS_TOOLS_DB_FIXTURE_PATH,
                f"metrics-{arrow.now().strftime('%Y-%m-%d-%H-%M-%S')}.db",
            )

        conn = duckdb.connect(database=database_path)

        conn.execute("CREATE SCHEMA metrics")

        # Create the events table if it doesn't already exist
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics.events_daily_to_artifact (
                bucket_day DATE,
                event_type STRING,
                event_source STRING,
                from_artifact_id STRING,
                to_artifact_id STRING,
                amount FLOAT
            )
        """
        )

        # Create the artifacts_to_projects_v1 table if it doesn't already exist
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics.artifacts_by_project_v1 (
                artifact_id STRING,
                artifact_source_id STRING,
                artifact_source STRING,
                artifact_namespace STRING,
                artifact_name STRING,
                project_id STRING,
                project_source STRING,
                project_namespace STRING,
                project_name STRING
            )
        """
        )

        # Create the projects_to_collections_v1 table if it doesn't already exist
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics.projects_by_collection_v1 (
                project_id STRING,
                project_source STRING,
                project_namespace STRING,
                project_name STRING,
                collection_id STRING,
                collection_source STRING,
                collection_namespace STRING,
                collection_name STRING
            )
        """
        )

        return cls(conn, encode_ids)

    def __init__(self, conn: duckdb.DuckDBPyConnection, encode_ids: bool):
        self._conn = conn
        self._encode_ids = encode_ids

    def encode_sha256_base64(self, input_str):
        """Helper method to encode a string to base64 SHA256 hash."""
        if not self._encode_ids:
            return input_str
        sha256_hash = hashlib.sha256(input_str.encode()).digest()
        return base64.b64encode(sha256_hash).decode()

    def generate_daily_events(
        self,
        start_ds: str,
        end_ds: str,
        event_type: str,
        from_artifact: str,
        to_artifact: str,
        event_source: str = "TEST",
        amount: float = 1.0,
        date_filter: t.Callable[[pd.DataFrame], pd.DataFrame] = lambda a: a,
    ):
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_ds, "%Y-%m-%d")
        end_date = datetime.strptime(end_ds, "%Y-%m-%d")
        date_range = pd.date_range(start=start_date, end=end_date)

        # Static values

        from_artifact_id = self.encode_sha256_base64(from_artifact)
        to_artifact_id = self.encode_sha256_base64(to_artifact)

        # Create DataFrame
        data = {
            "bucket_day": date_range,
            "event_type": event_type,
            "event_source": event_source,
            "from_artifact_id": from_artifact_id,
            "to_artifact_id": to_artifact_id,
            "amount": amount,
        }
        df = pd.DataFrame(data)  # noqa: F841
        df = date_filter(df)

        # Insert data into DuckDB table
        self._conn.execute(
            "INSERT INTO metrics.events_daily_to_artifact SELECT * FROM df"
        )

    def populate_artifacts_and_projects(
        self, projects: t.Dict[str, t.List[str]], collections: t.Dict[str, t.List[str]]
    ):
        """Populate artifacts_by_project_v1 and projects_by_collection_v1 tables."""

        # Prepare data for artifacts_by_project_v1
        artifacts_data = []
        for project_name, artifact_names in projects.items():
            project_id = self.encode_sha256_base64(project_name)
            for artifact_name in artifact_names:
                artifact_id = self.encode_sha256_base64(artifact_name)
                artifacts_data.append(
                    {
                        "artifact_id": artifact_id,
                        "artifact_source_id": "TEST",
                        "artifact_source": "TEST",
                        "artifact_namespace": "TEST",
                        "artifact_name": artifact_name,
                        "project_id": project_id,
                        "project_source": "TEST",
                        "project_namespace": "TEST",
                        "project_name": project_name,
                    }
                )

        # Insert data into artifacts_by_project_v1 table
        artifacts_df = pd.DataFrame(artifacts_data)  # noqa: F841
        self._conn.execute(
            "INSERT INTO metrics.artifacts_by_project_v1 SELECT * FROM artifacts_df"
        )

        # Prepare data for projects_by_collection_v1
        collections_data = []
        for collection_name, project_names in collections.items():
            collection_id = self.encode_sha256_base64(collection_name)
            for project_name in project_names:
                project_id = self.encode_sha256_base64(project_name)
                collections_data.append(
                    {
                        "project_id": project_id,
                        "project_source": "TEST",
                        "project_namespace": "TEST",
                        "project_name": project_name,
                        "collection_id": collection_id,
                        "collection_source": "TEST",
                        "collection_namespace": "TEST",
                        "collection_name": collection_name,
                    }
                )

        # Insert data into projects_by_collection_v1 table
        collections_df = pd.DataFrame(collections_data)  # noqa: F841
        self._conn.execute(
            "INSERT INTO metrics.projects_by_collection_v1 SELECT * FROM collections_df"
        )
