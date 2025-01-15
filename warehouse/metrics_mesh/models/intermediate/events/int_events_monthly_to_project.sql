MODEL (
  name metrics.int_events_monthly_to_project,
  description 'All events to a project, bucketed by month',
  kind FULL,
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
group by
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
