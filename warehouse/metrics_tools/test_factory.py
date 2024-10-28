import pytest

from .definition import MetricQueryDef, RollingConfig
from .factory import TimeseriesMetrics


@pytest.fixture
def timeseries_metrics_to_test():
    return TimeseriesMetrics.from_raw_options(
        start="2015-01-01",
        model_prefix="timeseries",
        metric_queries={
            # This will automatically generate star counts for the given roll up periods.
            # A time_aggregation is just a simple addition of the aggregation. So basically we
            # calculate the daily time_aggregation every day by getting the count of the day.
            # Then the weekly every week by getting the count of the week and
            # monthly by getting the count of the month.
            # Additionally this will also create this along the dimensions (entity_types) of
            # project/collection so the resulting models will be named as follows
            # `metrics.timeseries_stars_to_{entity_type}_{time_aggregation}`
            # "stars": MetricQueryDef(
            #     ref="stars.sql",
            #     time_aggregations=["daily", "weekly", "monthly"],
            # ),
            # This defines something with a rolling option that allows you to look back
            # to some arbitrary window. So you specify the window and specify the unit.
            # The unit and the window are used to pass in variables to the query. So it's
            # up to the query to actually query the correct window.
            # The resultant models are named as such
            # `metrics.timeseries_active_days_to_{entity_type}_over_{window}_{unit}`
            "developer_active_days": MetricQueryDef(
                ref="active_days.sql",
                vars={
                    "activity_event_types": ["COMMIT_CODE"],
                },
                rolling=RollingConfig(
                    windows=[30, 60, 90],
                    unit="day",
                    cron="@daily",  # This determines how often this is calculated
                ),
                entity_types=["artifact", "project", "collection"],
                is_intermediate=True,
            ),
            "developer_classifications": MetricQueryDef(
                ref="developer_activity_classification.sql",
                vars={
                    "full_time_ratio": 10 / 30,
                },
                rolling=RollingConfig(
                    windows=[30, 60, 90],
                    unit="day",
                    cron="@daily",
                ),
            ),
            # "contributor_classifications": MetricQueryDef(
            #     ref="contributor_activity_classification.sql",
            #     vars={"full_time_ratio": 10 / 30},
            #     rolling=RollingConfig(
            #         windows=[30, 60, 90],
            #         unit="day",
            #         cron="@daily",
            #     ),
            # ),
            # "active_addresses": MetricQueryDef(
            #     ref="active_addresses.sql",
            #     time_aggregations=["daily", "weekly", "monthly"],
            # ),
            # "commits": MetricQueryDef(
            #     ref="commits.sql",
            #     time_aggregations=["daily", "weekly", "monthly"],
            # ),
            # "forks": MetricQueryDef(
            #     ref="forks.sql",
            #     time_aggregations=["daily", "weekly", "monthly"],
            # ),
            # "gas_fees": MetricQueryDef(
            #     ref="gas_fees.sql",
            #     time_aggregations=["daily", "weekly", "monthly"],
            # ),
            # "change_in_developers": MetricQueryDef(
            #     ref="change_in_developers.sql",
            #     rolling=RollingConfig(
            #         windows=[30, 60, 90],
            #         unit="day",
            #         cron="@daily",
            #     ),
            # ),
        },
        default_dialect="clickhouse",
    )


def test_timeseries_metric_rendering(timeseries_metrics_to_test: TimeseriesMetrics):
    for name, query in timeseries_metrics_to_test.generate_queries().items():
        print(f"Query {name}:")
        print(query.sql("duckdb", pretty=True))
    assert False
