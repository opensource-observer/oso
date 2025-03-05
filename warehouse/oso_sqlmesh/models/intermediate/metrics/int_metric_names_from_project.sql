MODEL (
  name oso.int_metric_names_from_project,
  kind FULL
);

SELECT DISTINCT
  metric
FROM oso.timeseries_metrics_to_project