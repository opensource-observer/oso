MODEL (
  name oso.int_events_weekly__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_week,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("bucket_week"), "event_source", "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  )
);

SELECT
  DATE_TRUNC('WEEK', bucket_day) AS bucket_week,
  to_artifact_id,
  from_artifact_id,
  event_source,
  event_type,
  SUM(amount)
FROM oso.int_events_daily__github
WHERE
  bucket_day BETWEEN @start_date AND @end_date
GROUP BY
  1,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type