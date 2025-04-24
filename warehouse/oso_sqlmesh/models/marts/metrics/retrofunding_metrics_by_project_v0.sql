MODEL (
  name oso.retrofunding_metrics_by_project_v0,
  description "Retro Funding metrics by project for OP Atlas integration [unstable]",
  kind FULL,
  dialect trino,
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

WITH all_timeseries_metrics_by_project AS (
  SELECT
    @oso_id('OSO', 'oso', metric_name) AS metric_id,
    metric_name,
    project_id,
    sample_date,
    amount,
    unit
  FROM oso.int_superchain_s7_timeseries_metrics_by_project
)

SELECT
  metric_id::TEXT,
  metric_name::TEXT,
  project_id::TEXT,
  sample_date::DATE,
  amount::DOUBLE,
  unit::TEXT
FROM all_timeseries_metrics_by_project
