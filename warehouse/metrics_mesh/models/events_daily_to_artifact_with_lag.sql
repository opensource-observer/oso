MODEL (
  name metrics.events_daily_to_artifact_with_lag,
  kind FULL,
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
FROM metrics.events_daily_to_artifact