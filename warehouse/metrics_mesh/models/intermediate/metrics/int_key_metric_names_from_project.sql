MODEL (
  name metrics.int_key_metric_names_from_project,
  kind FULL
);

SELECT DISTINCT
  metric
FROM metrics.key_metrics_to_project