model(
    name oso.int_events_monthly_to_project,
    description 'All events to a project, bucketed by month',
    kind incremental_by_time_range(
        time_column bucket_month, batch_size 12, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@monthly',
    partitioned_by(month("bucket_month"), "event_type"),
    grain(bucket_month, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

select
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    timestamp_trunc(bucket_day, month) as bucket_month,
    sum(amount) as amount
from oso.int_events_daily_to_project
where bucket_day between @start_date and @end_date
group by
    project_id,
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    timestamp_trunc(bucket_day, month)
