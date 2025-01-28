MODEL (
  name metrics.key_metrics_by_collection_v0,
  kind FULL,
  tags (
  'export'
  )
);

WITH all_collection_key_metrics AS (
  SELECT * FROM metrics.int_metric_key_metrics_by_collection
),

key_metrics_by_collection_v0_no_casting AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_collection_id,
    -- TODO(jabolo): Check this with Reuven
    from_artifact_id as from_collection_id,
    metrics_sample_date AS sample_date,
    event_source,
    amount,
    metric,
    NULL AS unit
  FROM all_collection_key_metrics
)

SELECT
  metric_id::TEXT,
  to_collection_id::TEXT,
  from_collection_id::TEXT,
  sample_date::DATE,
  event_source::TEXT,
  amount::DOUBLE,
  metric::TEXT,
  unit::TEXT
FROM key_metrics_by_collection_v0_no_casting
