MODEL (
  name metrics.timeseries_metrics_by_artifact_v0,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 30
  ),
  cron "@daily",
  start "2015-01-01",
  dialect "clickhouse",
  grain (metric_id, artifact_id, sample_date),
);
WITH all_timeseries_metrics_by_artifact AS (
  SELECT @oso_id('OSO', 'oso', metric) AS metric_id,
    to_artifact_id AS artifact_id,
    bucket_day AS sample_date,
    amount AS amount,
    NULL AS unit
  FROM metrics.timeseries_metrics_by_artifact_over_30_days
)
SELECT metric_id::String,
  artifact_id::String,
  sample_date::Date,
  amount::Float64,
  unit
FROM all_timeseries_metrics_by_artifact