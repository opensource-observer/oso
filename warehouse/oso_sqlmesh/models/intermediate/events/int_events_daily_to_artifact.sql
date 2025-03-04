model(
    name oso.int_events_daily_to_artifact,
    kind incremental_by_time_range(
        time_column bucket_day, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("bucket_day"), "event_type"),
    grain(bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

with
    events as (
        select distinct
            from_artifact_id, to_artifact_id, event_source, event_type, time, amount
        from oso.int_events
        where
            time::date between strptime(@start_ds, '%Y-%m-%d')::date::date and strptime(
                @end_ds, '%Y-%m-%d'
            )::date::date
    )
select
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    date_trunc('DAY', time::date) as bucket_day,
    sum(amount) as amount
from events
group by
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    date_trunc('DAY', time::date)
