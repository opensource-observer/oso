MODEL (
  name metrics.int_events_to_project,
  description 'All events to a project',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

select
  artifacts.project_id,
  events.from_artifact_id,
  events.to_artifact_id,
  events.time,
  events.event_source,
  events.event_type,
  events.amount
from metrics.int_events events
inner join metrics.int_artifacts_by_project artifacts
  on
    events.to_artifact_id
    = artifacts.artifact_id
where events.time between @start_dt and @end_dt
