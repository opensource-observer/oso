MODEL (
  name metrics.events_daily_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 180,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (day("bucket_day"), "event_type"),
  grain (
    bucket_day,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id
  ),
);
WITH events AS (
  SELECT DISTINCT from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    time,
    amount
  from @oso_source.timeseries_events_by_artifact_v0
  where CAST(time AS DATE) between STR_TO_DATE(@start_ds, '%Y-%m-%d')::Date and STR_TO_DATE(@end_ds, '%Y-%m-%d')::Date
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