model(
    name oso.int_events_weekly_to_artifact,
    kind incremental_by_time_range(
        time_column bucket_week, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("bucket_week"), "event_source", "event_type"),
    grain(bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

select
    date_trunc('week', bucket_day) as bucket_week,
    to_artifact_id,
    from_artifact_id,
    event_source,
    event_type,
    sum(amount),
from oso.int_events_daily_to_artifact
where bucket_day between @start_date and @end_date
group by 1, from_artifact_id, to_artifact_id, event_source, event_type
