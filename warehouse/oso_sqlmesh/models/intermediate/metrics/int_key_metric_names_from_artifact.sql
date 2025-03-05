MODEL (
  name oso.int_key_metric_names_from_artifact,
  kind FULL
);

SELECT DISTINCT
  metric
FROM oso.key_metrics_to_artifact