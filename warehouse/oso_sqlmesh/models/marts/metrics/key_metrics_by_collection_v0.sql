MODEL (
  name oso.key_metrics_by_collection_v0,
  kind FULL,
  partitioned_by sample_date,
  tags (
    'export',
    'model_type=full',
    'model_category=metrics',
    'model_stage=mart'
  ),
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH key_metrics_by_collection_v0_no_casting AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_collection_id AS collection_id,
    metrics_sample_date AS sample_date,
    amount,
    metric,
    NULL AS unit
  FROM oso.key_metrics_to_collection
)
SELECT
  metric_id::TEXT,
  collection_id::TEXT,
  sample_date::DATE,
  amount::DOUBLE,
  unit::TEXT
FROM key_metrics_by_collection_v0_no_casting