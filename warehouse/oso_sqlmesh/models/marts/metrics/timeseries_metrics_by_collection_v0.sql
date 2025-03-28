MODEL (
  name oso.timeseries_metrics_by_collection_v0,
  kind FULL,
  partitioned_by sample_date,
  tags (
    'export',
    'model_type:full',
    'model_category:metrics',
    'model_stage:mart'
  )
);

WITH all_timeseries_metrics_by_collection AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_collection_id AS collection_id,
    metrics_sample_date AS sample_date,
    amount,
    metric,
    NULL AS unit
  FROM oso.key_metrics_to_collection
  UNION ALL
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_collection_id AS collection_id,
    metrics_sample_date AS sample_date,
    amount AS amount,
    NULL AS unit
  FROM oso.timeseries_metrics_to_collection
)
SELECT
  metric_id::TEXT,
  collection_id::TEXT,
  sample_date::DATE,
  amount::DOUBLE,
  unit::TEXT
FROM all_timeseries_metrics_by_collection