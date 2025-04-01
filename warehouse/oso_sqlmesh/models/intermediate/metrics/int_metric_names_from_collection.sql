MODEL (
  name oso.int_metric_names_from_collection,
  kind FULL,
  tags (
    "model_type=full",
    "model_category=metrics",
    "model_stage=intermediate"
  )
);

SELECT DISTINCT
  metric
FROM oso.timeseries_metrics_to_collection