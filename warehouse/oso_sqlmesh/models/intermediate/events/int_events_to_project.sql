model(
    name oso.int_events_to_project,
    description 'All events to a project',
    kind incremental_by_time_range(
        time_column time, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("time"), "event_type"),
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

select
    artifacts.project_id,
    events.from_artifact_id,
    events.to_artifact_id,
    events.time,
    events.event_source,
    events.event_type,
    events.amount
from oso.int_events events
inner join
    oso.int_artifacts_by_project artifacts
    on events.to_artifact_id = artifacts.artifact_id
where events.time between @start_dt and @end_dt
