MODEL (
  name oso.int_events_daily_to_project__github,
  description 'All events to a project, bucketed by day',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 2,
    lookback 31
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  tags (
    "entity_category=project",
    "github",
    "incremental"
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
    ),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
  )
);

SELECT
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time) AS bucket_day,
  SUM(amount) AS amount
FROM oso.int_events_to_project__github
WHERE
  time BETWEEN @start_dt AND @end_dt
GROUP BY
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time)