model(
    name oso.int_events_daily_to_project,
    description 'All events to a project, bucketed by day',
    kind incremental_by_time_range(
        time_column bucket_day, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("bucket_day"), "event_type"),
    grain(bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

select
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    timestamp_trunc(time, day) as bucket_day,
    sum(amount) as amount
from oso.int_events_to_project
where time between @start_dt and @end_dt
group by
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    timestamp_trunc(time, day)
