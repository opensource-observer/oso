from datetime import datetime

import duckdb
from metrics_tools.definition import PeerMetricDependencyRef
from metrics_tools.runner import MetricsRunner


def test_runner_rendering():
    runner = MetricsRunner.create_duckdb_execution_context(
        conn=duckdb.connect(),
        query="""
        select time from foo
        where time between @metrics_start('DATE') 
            and @metrics_end('DATE')
        """,
        ref=PeerMetricDependencyRef(
            name="test",
            entity_type="artifact",
            window=30,
            unit="day",
            cron="@monthly",
        ),
        locals={},
    )
    start = datetime.strptime("2024-01-01", "%Y-%m-%d")
    end = datetime.strptime("2024-12-31", "%Y-%m-%d")
    rendered = list(runner.render_rolling_queries(start, end))
    assert len(rendered) == 12
