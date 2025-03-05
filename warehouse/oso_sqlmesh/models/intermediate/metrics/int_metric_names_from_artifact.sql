MODEL (
  name oso.int_metric_names_from_artifact,
  kind FULL
);

SELECT DISTINCT
  metric
FROM oso.timeseries_metrics_to_artifact