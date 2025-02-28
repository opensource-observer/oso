MODEL (
  name metrics.int_events_to_collection,
  description 'All events to a collection',
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
  collections.collection_id,
  int_events_to_project.project_id,
  int_events_to_project.from_artifact_id,
  int_events_to_project.to_artifact_id,
  int_events_to_project.time,
  int_events_to_project.event_source,
  int_events_to_project.event_type,
  int_events_to_project.amount
from metrics.int_events_to_project
inner join metrics.int_projects_by_collection collections
  on int_events_to_project.project_id = collections.project_id
where int_events_to_project.time between @start_dt and @end_dt
