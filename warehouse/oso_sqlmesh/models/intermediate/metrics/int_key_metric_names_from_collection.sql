MODEL (
  name oso.int_key_metric_names_from_collection,
  kind FULL
);

SELECT DISTINCT
  metric
FROM oso.key_metrics_to_collection