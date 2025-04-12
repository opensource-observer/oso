MODEL (
  name oso.int_events_daily__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  event_source::VARCHAR,
  event_type::VARCHAR,
  SUM(amount::DOUBLE)::DOUBLE AS amount
FROM oso.int_events__github as events
WHERE time BETWEEN @start_dt AND @end_dt
GROUP BY
  DATE_TRUNC('DAY', time::DATE),
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type
