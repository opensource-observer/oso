MODEL (
  name oso.int_key_metric_names_from_project,
  kind FULL
);

SELECT DISTINCT
  metric
FROM oso.key_metrics_to_project