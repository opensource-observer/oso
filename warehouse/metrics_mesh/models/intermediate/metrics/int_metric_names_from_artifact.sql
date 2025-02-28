MODEL (
  name metrics.int_metric_names_from_artifact,
  kind FULL
);

SELECT DISTINCT
  metric
FROM metrics.timeseries_metrics_to_artifact