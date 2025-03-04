model(
    name oso.int_events,
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
    time,
    to_artifact_id,
    from_artifact_id,
    upper(event_type) as event_type,
    cast(event_source_id as string) as event_source_id,
    upper(event_source) as event_source,
    lower(to_artifact_name) as to_artifact_name,
    lower(to_artifact_namespace) as to_artifact_namespace,
    upper(to_artifact_type) as to_artifact_type,
    lower(to_artifact_source_id) as to_artifact_source_id,
    lower(from_artifact_name) as from_artifact_name,
    lower(from_artifact_namespace) as from_artifact_namespace,
    upper(from_artifact_type) as from_artifact_type,
    lower(from_artifact_source_id) as from_artifact_source_id,
    cast(amount as double) as amount
from
    (
        select *
        from @oso_source('bigquery.oso.int_events__blockchain')
        where time between @start_dt and @end_dt
        union all
        select *
        from oso.int_events__github
        where time between @start_dt and @end_dt
        union all
        select *
        from oso.int_events__dependencies
        where time between @start_dt and @end_dt
        union all
        select *
        from oso.int_events__funding
        where time between @start_dt and @end_dt
    )
