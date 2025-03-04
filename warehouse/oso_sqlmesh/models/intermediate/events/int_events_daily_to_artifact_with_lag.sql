model(
    name oso.int_events_daily_to_artifact_with_lag,
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
    bucket_day,
    to_artifact_id,
    from_artifact_id,
    event_source,
    event_type,
    amount,
    lag(bucket_day) over (
        partition by to_artifact_id, from_artifact_id, event_source, event_type
        order by bucket_day
    ) as last_event
from oso.int_events_daily_to_artifact
-- Only consider events from the last 2-3 years anything before would be
-- considered "new" or the first event should be used to determine any lifecycle 
where bucket_day between @start_date - interval 730 day and @end_date
