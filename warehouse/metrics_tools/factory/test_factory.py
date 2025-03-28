import os

import arrow
import pytest
from metrics_tools.definition import MetricQueryDef, RollingConfig
from metrics_tools.runner import MetricsRunner
from metrics_tools.utils.dataframes import as_pandas_df
from metrics_tools.utils.fixtures.gen_data import MetricsDBFixture
from metrics_tools.utils.testing import duckdb_df_context

from .factory import TimeseriesMetrics

CURR_DIR = os.path.dirname(__file__)


@pytest.fixture
def timeseries_duckdb():
    # initial duckdb with some basic timeseries metrics
    fixture = MetricsDBFixture.create()
    fixture.populate_artifacts_and_projects(
        projects={
            "p_0": ["service_0", "service_1", "service_2", "repo_0", "repo_1"],
            "p_1": ["service_3", "service_4", "repo_2", "repo_3"],
            "p_2": ["service_5", "repo_5"],
        },
        collections={
            "c_0": ["p_0"],
            "c_1": ["p_1", "p_2"],
            "c_3": ["p_0", "p_1", "p_2"],
        },
    )
    start = "2023-12-01"
    end = "2025-02-01"

    fixture.generate_daily_events(start, end, "VISIT", "user_0", "service_0")
    fixture.generate_daily_events(start, end, "VISIT", "user_0", "service_1")
    fixture.generate_daily_events(start, end, "VISIT", "user_1", "service_1")
    fixture.generate_daily_events(start, end, "VISIT", "user_2", "service_2")

    for ft_dev_index in range(5):
        dev_name = f"ft_dev_{ft_dev_index}"
        fixture.generate_daily_events(start, end, "COMMIT_CODE", dev_name, "repo_0")

    # Change in developers
    for ft_dev_index in range(5, 10):
        dev_name = f"ft_dev_{ft_dev_index}"
        fixture.generate_daily_events(
            start,
            end,
            "COMMIT_CODE",
            dev_name,
            "repo_0",
            date_filter=lambda df: as_pandas_df(df[df["bucket_day"].dt.day <= 7]),
        )

    for ft_dev_index in range(5):
        dev_name = f"ft_dev_{ft_dev_index}"
        fixture.generate_daily_events(start, end, "COMMIT_CODE", dev_name, "repo_1")

    # User that commits only once a month
    for pt_dev_index in range(10):
        dev_name = f"pt_dev_{pt_dev_index}"
        fixture.generate_daily_events(
            start,
            end,
            "COMMIT_CODE",
            dev_name,
            "repo_0",
            date_filter=lambda df: as_pandas_df(df[df["bucket_day"].dt.day % 5 == 0]),
        )
    yield fixture
    fixture._conn.close()


@pytest.fixture
def timeseries_metrics_to_test():
    return TimeseriesMetrics.from_raw_options(
        start="2024-01-01",
        schema="oso",
        model_prefix="timeseries",
        metric_queries={
            "visits": MetricQueryDef(
                ref="visits.sql",
                time_aggregations=[
                    "daily",
                    "weekly",
                    "monthly",
                    "quarterly",
                    "biannually",
                    "yearly",
                ],
                rolling=RollingConfig(
                    windows=[7],
                    unit="day",
                    cron="@daily",
                ),
                over_all_time=True,
                entity_types=["artifact", "project", "collection"],
            ),
            "developer_active_days": MetricQueryDef(
                ref="active_days.sql",
                vars={
                    "activity_event_types": ["COMMIT_CODE"],
                },
                rolling=RollingConfig(
                    windows=[7, 14],
                    unit="day",
                    cron="@daily",  # This determines how often this is calculated
                ),
                # entity_types=["artifact", "project", "collection"],
                entity_types=["artifact", "project", "collection"],
                is_intermediate=True,
            ),
            "developer_classifications": MetricQueryDef(
                ref="developer_activity_classification.sql",
                vars={
                    "full_time_ratio": 10 / 30,
                },
                rolling=RollingConfig(
                    windows=[7, 14],
                    unit="day",
                    cron="@daily",
                ),
                entity_types=["artifact", "project", "collection"],
            ),
            "change_in_7_day_developer_activity": MetricQueryDef(
                ref="change_in_developers.sql",
                vars={
                    "comparison_interval": 7,
                },
                rolling=RollingConfig(
                    windows=[2],
                    unit="period",
                    cron="@daily",
                ),
                entity_types=["artifact", "project", "collection"],
            ),
        },
        default_dialect="trino",
        queries_dir=os.path.join(CURR_DIR, "fixtures/metrics"),
        timeseries_sources=["events_daily_to_artifact"],
    )


def test_timeseries_metric_rendering(timeseries_metrics_to_test: TimeseriesMetrics):
    queries = timeseries_metrics_to_test.generate_queries()
    for name, query_config in queries.items():
        query = query_config["rendered_query"]
        print(f"Query {name}:")
        print(query.sql("duckdb", pretty=True))

    table_names = set(queries.keys())
    assert table_names == {
        "visits_to_artifact_daily",
        "visits_to_project_daily",
        "visits_to_collection_daily",
        "visits_to_artifact_weekly",
        "visits_to_project_weekly",
        "visits_to_collection_weekly",
        "visits_to_artifact_monthly",
        "visits_to_project_monthly",
        "visits_to_collection_monthly",
        "visits_to_artifact_quarterly",
        "visits_to_project_quarterly",
        "visits_to_collection_quarterly",
        "visits_to_artifact_biannually",
        "visits_to_project_biannually",
        "visits_to_collection_biannually",
        "visits_to_artifact_yearly",
        "visits_to_project_yearly",
        "visits_to_collection_yearly",
        "visits_to_artifact_over_all_time",
        "visits_to_project_over_all_time",
        "visits_to_collection_over_all_time",
        "visits_to_artifact_over_7_day_window",
        "visits_to_project_over_7_day_window",
        "visits_to_collection_over_7_day_window",
        "developer_active_days_to_artifact_over_7_day_window",
        "developer_active_days_to_project_over_7_day_window",
        "developer_active_days_to_collection_over_7_day_window",
        "developer_active_days_to_artifact_over_14_day_window",
        "developer_active_days_to_project_over_14_day_window",
        "developer_active_days_to_collection_over_14_day_window",
        "developer_classifications_to_artifact_over_7_day_window",
        "developer_classifications_to_project_over_7_day_window",
        "developer_classifications_to_collection_over_7_day_window",
        "developer_classifications_to_artifact_over_14_day_window",
        "developer_classifications_to_project_over_14_day_window",
        "developer_classifications_to_collection_over_14_day_window",
        "change_in_7_day_developer_activity_to_artifact_over_2_period_window",
        "change_in_7_day_developer_activity_to_project_over_2_period_window",
        "change_in_7_day_developer_activity_to_collection_over_2_period_window",
    }


def test_with_runner(
    timeseries_metrics_to_test: TimeseriesMetrics, timeseries_duckdb: MetricsDBFixture
):
    base_locals = {"oso_source": "sources"}
    connection = timeseries_duckdb._conn

    for _, query_config, _ in timeseries_metrics_to_test.generate_ordered_queries():
        ref = query_config["ref"]
        locals = query_config["vars"].copy()
        locals.update(base_locals)
        runner = MetricsRunner.create_duckdb_execution_context(
            connection,
            [query_config["rendered_query"]],
            ref,
            locals,
        )
        runner.commit(
            arrow.get("2024-01-01").datetime,
            arrow.get("2024-01-16").datetime,
            f"oso.{query_config['table_name']}",
        )

    # Data assertions
    # Validate that the daily visits are correct
    with duckdb_df_context(
        connection,
        """
        SELECT * 
        FROM oso.visits_to_artifact_daily 
        where metrics_sample_date = '2024-01-15'
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "service_0"]
        assert df.iloc[0]["amount"] == 1

    # Validate that quarterly visits are correct
    with duckdb_df_context(
        connection,
        """
        SELECT * 
        FROM oso.visits_to_artifact_quarterly
        where metrics_sample_date = '2024-01-01'
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "service_0"]
        assert df.iloc[0]["amount"] == 91

    # Validate that biannual visits are correct
    with duckdb_df_context(
        connection,
        """
        SELECT * 
        FROM oso.visits_to_artifact_biannually
        where metrics_sample_date = '2024-01-01'
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "service_0"]
        assert df.iloc[0]["amount"] == 182

    # Validate that the yearly visits are correct
    with duckdb_df_context(
        connection,
        """
        SELECT * 
        FROM oso.visits_to_artifact_yearly
        where metrics_sample_date = '2024-01-01'
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "service_0"]
        assert df.iloc[0]["amount"] == 366

    # Validate that the rolling window visits are correct
    with duckdb_df_context(
        connection,
        """
        SELECT * 
        FROM oso.visits_to_artifact_over_7_day_window
        where metrics_sample_date = '2024-01-15'
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "service_0"]
        assert df.iloc[0]["amount"] == 7

    # Validate visits over all time
    with duckdb_df_context(
        connection,
        """
        SELECT * 
        FROM oso.visits_to_artifact_over_all_time
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "service_0"]
        assert df.iloc[0]["amount"] == 429

    with duckdb_df_context(
        connection,
        """
    SELECT * 
    FROM oso.developer_active_days_to_artifact_over_7_day_window 
    where metrics_sample_date = '2024-01-08'
    """,
    ) as df:
        repo0_df = as_pandas_df(df[df["to_artifact_id"] == "repo_0"])
        dev0_df = as_pandas_df(repo0_df[repo0_df["from_artifact_id"] == "ft_dev_0"])
        assert dev0_df.iloc[0]["amount"] == 7
        dev5_df = as_pandas_df(repo0_df[repo0_df["from_artifact_id"] == "ft_dev_5"])
        assert dev5_df.iloc[0]["amount"] == 6

    with duckdb_df_context(
        connection,
        """
    SELECT * 
    FROM oso.developer_active_days_to_project_over_14_day_window 
    where metrics_sample_date = '2024-01-15'
    """,
    ) as df:
        p0_df = as_pandas_df(df[df["to_project_id"] == "p_0"])
        p0_dev0_df = as_pandas_df(p0_df[p0_df["from_artifact_id"] == "ft_dev_0"])
        assert p0_dev0_df.iloc[0]["amount"] == 14

    with duckdb_df_context(
        connection,
        """
    SELECT * 
    FROM oso.developer_classifications_to_artifact_over_14_day_window 
    where metrics_sample_date = '2024-01-15' and metric = 'full_time_developers_over_14_day_window'
    """,
    ) as df:
        df = df[df["to_artifact_id"] == "repo_0"]
        assert df.iloc[0]["amount"] == 10

    with duckdb_df_context(
        connection,
        """
    SELECT * 
    FROM oso.developer_classifications_to_artifact_over_14_day_window 
    where metrics_sample_date = '2024-01-15'
    """,
    ) as df:
        assert len(df) == 6
        df = df[df["to_artifact_id"] == "repo_0"]
        assert df.iloc[0]["amount"] == 10

    with duckdb_df_context(
        connection,
        """
    SELECT * 
    FROM oso.change_in_7_day_developer_activity_to_artifact_over_2_period_window 
    where metrics_sample_date = '2024-01-15'
    """,
    ) as df:
        assert len(df) == 6
        df = df[df["to_artifact_id"] == "repo_0"]
        assert df.iloc[0]["amount"] == -5
