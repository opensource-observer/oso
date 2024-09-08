from metrics_mesh.lib.factories import (
    MetricQueryDef,
    timeseries_metrics,
)


# daily_timeseries_rolling_window_model(
#     model_name="metrics.timeseries_metrics_by_artifact_over_30_days",
#     metric_queries={
#         "developer_active_days": MetricQueryDef(
#             ref="active_days.sql",
#             vars={
#                 "activity_event_types": ["COMMIT_CODE"],
#             },
#         ),
#         "developer_classifications": MetricQueryDef(
#             ref="developer_activity_classification.sql",
#             vars={"full_time_days": 10},
#         ),
#         "contributor_active_days": MetricQueryDef(
#             ref="active_days.sql",
#             vars={
#                 "activity_event_types": [
#                     "COMMIT_CODE",
#                     "ISSUE_OPENED",
#                     "PULL_REQUEST_OPENED",
#                 ],
#             },
#         ),
#         "contributor_classifications": MetricQueryDef(
#             ref="contributor_activity_classification.sql",
#             vars={"full_time_days": 10},
#         ),
#         "stars": MetricQueryDef(
#             ref="stars.sql",
#             vars={},
#         ),
#     },
#     trailing_days=30,
#     model_options=dict(
#         start="2015-01-01",
#         cron="@daily",
#     ),
# )

timeseries_metrics(
    model_prefix="timeseries",
    metric_queries={
        "stars": MetricQueryDef(
            ref="stars.sql",
            vars={},
            trailing_windows=[30],
            entity_types=["artifact"],
        )
    },
    default_dialect="clickhouse",
)
