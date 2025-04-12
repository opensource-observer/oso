MODEL (
  name oso.int_metric_names_from_collection,
  kind FULL,
  tags (
    "model_type=full",
    "model_category=metrics",
    "model_stage=intermediate"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  metric
FROM oso.timeseries_metrics_to_collection