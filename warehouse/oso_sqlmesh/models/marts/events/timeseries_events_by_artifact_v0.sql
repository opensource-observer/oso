model(
    name oso.timeseries_events_by_artifact_v0,
    kind incremental_by_time_range(
        time_column time, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id),
    partitioned_by(day("time"), "event_type")
)
;

select
    time,
    to_artifact_id,
    from_artifact_id,
    event_type,
    event_source_id,
    event_source,
    amount
from oso.int_events
where time between @start_dt and @end_dt
