MODEL (
  name oso.timeseries_metrics_by_project_v0,
  kind FULL,
  partitioned_by sample_date,
  tags (
    'export',
    'model_type:full',
    'model_category:metrics',
    'model_stage:mart'
  )
);

WITH all_key_metrics_by_project AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_project_id AS project_id,
    metrics_sample_date AS sample_date,
    amount,
    NULL AS unit
  FROM oso.key_metrics_to_project
),
all_timeseries_metrics_by_project AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_project_id AS project_id,
    metrics_sample_date AS sample_date,
    amount AS amount,
    NULL AS unit
  FROM oso.timeseries_metrics_to_project
),
unioned_metrics_by_project AS (
  SELECT * FROM all_key_metrics_by_project
  UNION ALL
  SELECT * FROM all_timeseries_metrics_by_project
)

SELECT
  metric_id::TEXT,
  project_id::TEXT,
  sample_date::DATE,
  amount::DOUBLE,
  unit::TEXT
FROM unioned_metrics_by_project