MODEL (
  name metrics.last_of_event_from_artifact,
  kind FULL,
  partitioned_by (year("time"), "event_type", "event_source"),
  grain (
    time,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id
  ),
);
select MAX(time) as time,
  event_type,
  event_source,
  from_artifact_id,
  to_artifact_id
from @oso_source('timeseries_events_by_artifact_v0')
group by event_type,
  event_source,
  from_artifact_id,
  to_artifact_id