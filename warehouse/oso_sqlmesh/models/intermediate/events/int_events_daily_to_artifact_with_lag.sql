MODEL (
  name metrics.int_events_daily_to_artifact_with_lag,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  bucket_day,
  to_artifact_id,
  from_artifact_id,
  event_source,
  event_type,
  amount,
  LAG(bucket_day) OVER (PARTITION BY to_artifact_id, from_artifact_id, event_source, event_type ORDER BY bucket_day) AS last_event
FROM metrics.int_events_daily_to_artifact
-- Only consider events from the last 2-3 years anything before would be
-- considered "new" or the first event should be used to determine any lifecycle 
WHERE bucket_day between @start_date - INTERVAL 730 DAY AND @end_date
