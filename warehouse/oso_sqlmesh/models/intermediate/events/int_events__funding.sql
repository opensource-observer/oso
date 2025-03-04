model(
    name oso.int_events__funding,
    dialect trino,
    kind incremental_by_time_range(
        time_column time, batch_size 90, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("time"), "event_type"),
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

with
    open_collective_expenses as (
        select
            time,
            event_type,
            event_source_id,
            event_source,
            to_artifact_id,
            to_name,
            to_namespace,
            to_type,
            to_artifact_source_id,
            from_artifact_id,
            from_name,
            from_namespace,
            from_type,
            from_artifact_source_id,
            amount
        from oso.stg_open_collective__expenses
        where unit = 'USD' and time between @start_dt and @end_dt
    ),

    open_collective_deposits as (
        select
            time,
            event_type,
            event_source_id,
            event_source,
            to_artifact_id,
            to_name,
            to_namespace,
            to_type,
            to_artifact_source_id,
            from_artifact_id,
            from_name,
            from_namespace,
            from_type,
            from_artifact_source_id,
            amount
        from oso.stg_open_collective__deposits
        where unit = 'USD' and time between @start_dt and @end_dt
    ),

    all_funding_events as (
        select *
        from open_collective_expenses
        union all
        select *
        from open_collective_deposits
    )

select
    time,
    to_artifact_id,
    from_artifact_id,
    upper(event_type) as event_type,
    cast(event_source_id as string) as event_source_id,
    upper(event_source) as event_source,
    lower(to_name) as to_artifact_name,
    lower(to_namespace) as to_artifact_namespace,
    upper(to_type) as to_artifact_type,
    lower(to_artifact_source_id) as to_artifact_source_id,
    lower(from_name) as from_artifact_name,
    lower(from_namespace) as from_artifact_namespace,
    upper(from_type) as from_artifact_type,
    lower(from_artifact_source_id) as from_artifact_source_id,
    cast(amount as double) as amount
from all_funding_events
