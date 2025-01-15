MODEL (
  name metrics.int_events_daily_to_project,
  description 'All events to a project, bucketed by day',
  kind FULL,
);

select
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from metrics.int_events_to_project
group by
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day)
