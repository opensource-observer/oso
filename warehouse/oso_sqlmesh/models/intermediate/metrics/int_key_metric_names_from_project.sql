MODEL (
  name oso.int_key_metric_names_from_project,
  kind FULL,
  tags (
    "model_type:full",
    "model_category:metrics",
    "model_stage:intermediate"
  )
);

SELECT DISTINCT
  metric
FROM oso.key_metrics_to_project