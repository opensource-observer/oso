MODEL (
  name metrics.int_key_metric_names_from_artifact,
  kind FULL
);

SELECT DISTINCT
  metric
FROM metrics.key_metrics_to_artifact