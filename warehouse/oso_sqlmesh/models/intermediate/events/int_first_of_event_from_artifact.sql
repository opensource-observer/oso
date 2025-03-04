model(
    name oso.int_first_of_event_from_artifact,
    kind full,
    partitioned_by(year("time"), "event_type", "event_source"),
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

select
    min(bucket_week) as time, event_type, event_source, from_artifact_id, to_artifact_id
from oso.int_events_weekly_to_artifact
group by event_type, event_source, from_artifact_id, to_artifact_id
