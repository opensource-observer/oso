MODEL (
  name oso.key_metrics_by_project_v0,
  kind FULL,
  partitioned_by year(sample_date),
  tags (
    'export',
    'model_type=full',
    'model_category=metrics',
    'model_stage=mart',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH key_metrics_by_project_v0_no_casting AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_project_id AS project_id,
    metrics_sample_date AS sample_date,
    amount,
    metric,
    NULL AS unit
  FROM oso.key_metrics_to_project
)
SELECT
  metric_id::TEXT,
  project_id::TEXT,
  sample_date::DATE,
  amount::DOUBLE,
  unit::TEXT
FROM key_metrics_by_project_v0_no_casting
