MODEL (
  name oso.int_events_weekly__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_week,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_week"), "event_type"),
  grain (bucket_week, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_week,
      no_gap_date_part := 'week',
      ignore_before := DATE('2020-01-01'),
      missing_rate_min_threshold := 0.95,
    ),
  ),
  tags (
    "github",
    "incremental",
  ),
);

SELECT
  DATE_TRUNC('WEEK', bucket_day) AS bucket_week,
  to_artifact_id,
  from_artifact_id,
  event_source,
  event_type,
  SUM(amount) AS amount
FROM oso.int_events_daily__github
WHERE
  bucket_day BETWEEN @start_dt AND @end_dt
GROUP BY
  1,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type