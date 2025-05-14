MODEL (
  name oso.int_events_monthly_to_project__github,
  description 'All events to a project, bucketed by month',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_month,
    batch_size 12,
    batch_concurrency 1,
    lookback 1
  ),
  start '2015-01-01',
  cron '@monthly',
  partitioned_by (MONTH("bucket_month"), "event_type"),
  grain (bucket_month, event_type, event_source, from_artifact_id, to_artifact_id),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_month,
      no_gap_date_part := 'month',
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
  DATE_TRUNC('MONTH', bucket_day) AS bucket_month,
  SUM(amount) AS amount
FROM oso.int_events_daily_to_project__github
WHERE
  bucket_day BETWEEN @start_date AND @end_date
GROUP BY
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('MONTH', bucket_day)