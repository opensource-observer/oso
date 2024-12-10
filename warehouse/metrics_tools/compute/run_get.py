# Testing script
import logging
import click
from datetime import datetime
from metrics_tools.compute.client import Client
import requests
from pydantic_core import to_jsonable_python

from .types import (
    ClusterStartRequest,
    ExportReference,
    ExportType,
    ExportedTableLoadRequest,
    QueryJobSubmitRequest,
)
from ..definition import PeerMetricDependencyRef

logger = logging.getLogger(__name__)


def run_get(
    url: str,
    start: str,
    end: str,
    batch_size: int = 1,
):
    input = QueryJobSubmitRequest(
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
    # requests.get(f"{url}/sub", json=input.dict())
    response = requests.post(f"{url}/job/submit", json=to_jsonable_python(input))
    print(response.json())


def run_start(url: str, min=6, max=10):
    req = ClusterStartRequest(min_size=min, max_size=max)
    response = requests.post(f"{url}/cluster/start", json=to_jsonable_python(req))
    print(response.json())


def run_cache_load(url: str):
    req = ExportedTableLoadRequest(
        map={
            "sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958": ExportReference(
                table="export_metrics__events_daily_to_artifact__2357434958_5def5e890a984cf99f7364ce3c2bb958",
                type=ExportType.GCS,
                payload={
                    "gcs_path": "gs://oso-dataset-transfer-bucket/trino-export/export_metrics__events_daily_to_artifact__2357434958_5def5e890a984cf99f7364ce3c2bb958"
                },
            ),
        }
    )
    response = requests.post(f"{url}/cache/manual", json=to_jsonable_python(req))
    print(response.json())


def run_stop(url: str):
    response = requests.post(f"{url}/cluster/stop")
    print(response.json())


def run_get_status(url: str, job_id: str):
    response = requests.get(f"{url}/job/status/{job_id}")
    print(response.json())


def run_local_test(
    url: str, start: str, end: str, batch_size: int, cluster_size: int = 6
):
    import sys

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    client = Client(url, log_override=logger)

    client.run_cache_manual_load(
        {
            "sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958": ExportReference(
                table="export_metrics__events_daily_to_artifact__2357434958_5def5e890a984cf99f7364ce3c2bb958",
                type=ExportType.GCS,
                payload={
                    "gcs_path": "gs://oso-dataset-transfer-bucket/trino-export/export_metrics__events_daily_to_artifact__2357434958_5def5e890a984cf99f7364ce3c2bb958"
                },
            ),
        }
    )

    client.calculate_metrics(
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
        cluster_max_size=cluster_size,
        cluster_min_size=cluster_size,
    )


@click.command()
@click.option("--url", default="http://localhost:8000")
@click.option("--batch-size", type=click.INT, default=1)
@click.option("--start", default="2024-01-01")
@click.option("--cluster-size", type=click.INT, default=6)
@click.option("--end")
def main(url: str, batch_size: int, start: str, end: str, cluster_size: int):
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    run_local_test(
        url,
        start,
        end,
        batch_size,
        cluster_size=cluster_size,
    )


if __name__ == "__main__":
    main()
