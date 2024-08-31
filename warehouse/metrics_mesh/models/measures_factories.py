from metrics_mesh.lib.factories import (
    daily_timeseries_rolling_window_model,
    MetricQuery,
)

daily_timeseries_rolling_window_model(
    model_name="metrics.timeseries_code_metrics_by_artifact_over_30_days",
    metric_queries={
        "developer_active_days": MetricQuery(
            ref="active_days.sql",
            vars={
                "activity_event_type": "COMMIT_CODE",
            },
        ),
        "developer_classifications": MetricQuery(
            ref="developer_activity_classification.sql",
            vars={"full_time_days": 10},
        ),
    },
    trailing_days=30,
)
