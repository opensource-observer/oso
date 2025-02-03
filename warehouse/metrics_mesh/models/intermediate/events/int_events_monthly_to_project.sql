MODEL (
  name metrics.int_events_monthly_to_project,
  description 'All events to a project, bucketed by month',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_month,
    batch_size 12,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@monthly',
  partitioned_by (MONTH("bucket_month"), "event_type"),
  grain (bucket_month, event_type, event_source, from_artifact_id, to_artifact_id)
);

select
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month) as bucket_month,
  SUM(amount) as amount
from metrics.int_events_daily_to_project
where bucket_day between @start_date and @end_date
group by
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
