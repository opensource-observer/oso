# Testing script
import click
from datetime import datetime
import requests

from .types import QueryJobSubmitInput
from ..definition import PeerMetricDependencyRef


def run_get(
    url: str,
    start: str,
    end: str,
    batch_size: int = 1,
):
    input = QueryJobSubmitInput(
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
    response = requests.post(f"{url}/job/submit", json=input.model_dump_json())
    print(response.json())


@click.command()
@click.option("--url", default="http://localhost:8000")
@click.option("--batch-size", type=click.INT, default=1)
@click.option("--start", default="2024-01-01")
@click.option("--end")
def main(url: str, batch_size: int, start, end):
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    run_get(url, batch_size=batch_size, start=start, end=end)


if __name__ == "__main__":
    main()
