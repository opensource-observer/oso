MODEL (
  name metrics.int_metric_names_from_collection,
  kind FULL
);

SELECT DISTINCT
  metric
FROM metrics.timeseries_metrics_to_collection