MODEL (
  name oso.int_events_daily__github_with_lag,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    not_null(columns := (event_type, event_source)),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "github",
    "incremental"
  )
);

SELECT
  bucket_day,
  to_artifact_id,
  from_artifact_id,
  event_source,
  event_type,
  amount,
  LAG(bucket_day) OVER (PARTITION BY to_artifact_id, from_artifact_id, event_source, event_type ORDER BY bucket_day) AS last_event
FROM oso.int_events_daily__github
/* Only consider events from the last 2-3 years anything before would be */ /* considered "new" or the first event should be used to determine any lifecycle */
WHERE
  bucket_day BETWEEN @start_date - INTERVAL '730' DAY AND @end_date