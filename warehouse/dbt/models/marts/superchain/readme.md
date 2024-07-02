# Metrics for Optimism Retro Funding 4

Official summary metrics are displayed in the `rf4_impact_metrics_by_project` table, indexed by `application_id`. The model consolidates the 13 individual metrics in the `metrics/` directory and applies a log transformation to an additional 3, yielding a total of 16 metrics.

All metrics are derived from the following event models:

- `rf4_events_by_project`: relevant onchain events for each project over the RF4 transaction window (derived from transaction data)
- `rf4_4337_events`: relevant 4337-related events for each project over the RF4 transaction window (derived from trace data)

Finally, the `rf4_trusted_users` model includes the source data and heuristics used to identify trusted users.

The `rf4_repo_stats_by_project` model is a temporary model used to assist reviewers in determining the open source status of projects. It is not used in the final metrics. Similarly, all models in the `verification/` directory were used to verify project activity before the review phase, and are not used in the final metrics.

## Additional resources

- Full write-up on the process OSO employed to calculate metrics: https://docs.opensource.observer/blog/impact-metrics-rf4-deep-dive/
- Interactive version of the RF4 metrics models: https://models.opensource.observer/#!/model/model.opensource_observer.rf4_impact_metrics_by_project
