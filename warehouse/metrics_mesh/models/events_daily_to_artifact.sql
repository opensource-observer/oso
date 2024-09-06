MODEL (
  name metrics.events_daily_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 30
  ),
  start '2015-01-01',
  cron '@daily',
  dialect 'clickhouse',
  grain (
    bucket_day,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id
  ),
  columns (
    bucket_day DATE,
    event_source String,
    event_type String,
    from_artifact_id String,
    to_artifact_id String,
    amount Float64
  )
);
WITH events AS (
  SELECT DISTINCT from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    time,
    amount
  FROM @source("oso", "timeseries_events_by_artifact_v0")
  WHERE time::DATE BETWEEN STR_TO_DATE(@start_ds, '%Y-%m-%d')::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime) AND STR_TO_DATE(@end_ds, '%Y-%m-%d')::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)::Nullable(DateTime)
)
SELECT from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  SUM(amount) AS amount
FROM events
GROUP BY from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE)