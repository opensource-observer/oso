MODEL (
  name metrics.int_events_to_project,
  kind FULL,
  description 'All events to a project',
);

select
  artifacts.project_id,
  events.from_artifact_id,
  events.to_artifact_id,
  events.time,
  events.event_source,
  events.event_type,
  events.amount
from @oso_source('timeseries_events_by_artifact_v0') events
inner join @oso_source('artifacts_by_project_v1') artifacts
  on
    events.to_artifact_id
    = artifacts.artifact_id
