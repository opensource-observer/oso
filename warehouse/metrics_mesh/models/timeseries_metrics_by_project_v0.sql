MODEL (
  name metrics.timeseries_metrics_by_project_v0,
  kind VIEW
);
WITH all_timeseries_metrics_by_project AS (
  SELECT @oso_id('OSO', 'oso', metric) AS metric_id,
    to_project_id AS project_id,
    metrics_sample_date AS sample_date,
    amount AS amount,
    NULL AS unit
  FROM metrics.timeseries_metrics_to_project
)
SELECT metric_id::String,
  project_id::String,
  sample_date::Date,
  amount::Float64,
  unit::Nullable(String)
FROM all_timeseries_metrics_by_project