MODEL (
  name metrics.key_metrics_by_artifact_v0,
  kind FULL,
  tags (
  'export'
  )
);

WITH all_artifact_key_metrics AS (
  SELECT * FROM metrics.int_metric_key_metrics_by_artifact
),

key_metrics_by_artifact_v0_no_casting AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_artifact_id,
    from_artifact_id,
    metrics_sample_date AS sample_date,
    event_source,
    amount,
    metric,
    NULL AS unit
  FROM all_artifact_key_metrics
)

SELECT
  metric_id::TEXT,
  to_artifact_id::TEXT,
  from_artifact_id::TEXT,
  sample_date::DATE,
  event_source::TEXT,
  amount::DOUBLE,
  metric::TEXT,
  unit::TEXT
FROM key_metrics_by_artifact_v0_no_casting
