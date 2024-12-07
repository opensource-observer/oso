# Testing script
import click
from datetime import datetime
import requests
from pydantic_core import to_jsonable_python

from .types import ClusterStartRequest, ExportedTableLoad, QueryJobSubmitRequest
from ..definition import PeerMetricDependencyRef


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
    req = ExportedTableLoad(
        map={
            "sqlmesh__metrics.metrics__events_daily_to_artifact__2357434958": "export_metrics__events_daily_to_artifact__2357434958_5def5e890a984cf99f7364ce3c2bb958",
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


@click.command()
@click.option("--url", default="http://localhost:8000")
@click.option("--batch-size", type=click.INT, default=1)
@click.option("--start", default="2024-01-01")
@click.option("--end")
def main(url: str, batch_size: int, start, end):
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    run_start(url, 8, 8)
    run_cache_load(url)
    run_get(url, batch_size=batch_size, start=start, end=end)


if __name__ == "__main__":
    main()
