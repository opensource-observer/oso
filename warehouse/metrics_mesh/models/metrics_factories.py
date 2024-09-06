from metrics_mesh.lib.factories import (
    daily_timeseries_rolling_window_model,
    MetricQuery,
)


daily_timeseries_rolling_window_model(
    model_name="metrics.timeseries_metrics_by_artifact_over_30_days",
    metric_queries={
        "developer_active_days": MetricQuery(
            ref="active_days.sql",
            vars={
                "activity_event_types": ["COMMIT_CODE"],
            },
        ),
        "developer_classifications": MetricQuery(
            ref="developer_activity_classification.sql",
            vars={"full_time_days": 10},
        ),
        "contributor_active_days": MetricQuery(
            ref="active_days.sql",
            vars={
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                ],
            },
        ),
        "contributor_classifications": MetricQuery(
            ref="contributor_activity_classification.sql",
            vars={"full_time_days": 10},
        ),
        "stars": MetricQuery(
            ref="stars.sql",
            vars={},
        ),
    },
    trailing_days=30,
    model_options=dict(
        start="2015-01-01",
        cron="@daily",
    ),
)
