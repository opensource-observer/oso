MODEL (
  name oso.int_key_metric_names_from_collection,
  kind FULL,
  tags (
    "model_type=full",
    "model_category=metrics",
    "model_stage=intermediate"
  ),
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT DISTINCT
  metric
FROM oso.key_metrics_to_collection