model(
    name oso.int_events__dependencies,
    dialect trino,
    kind incremental_by_time_range(
        time_column time, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("time"), "event_type"),
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

@def(event_source_name, 'DEPS_DEV')
;

with
    artifacts as (
        select artifact_name from oso.int_all_artifacts where artifact_source = 'NPM'
    ),

    snapshots as (
        select
            snapshotat as time,
            system as from_artifact_type,
            name as from_artifact_name,
            version as from_artifact_version,
            dependency.name as to_artifact_name,
            dependency.system as to_artifact_type,
            dependency.version as to_artifact_version,
            lag(dependency.name) over (
                partition by system, name, dependency.name, version, dependency.version
                order by snapshotat
            ) as previous_to_artifact_name
        from @oso_source('bigquery.oso.stg_deps_dev__dependencies')
        where
            minimumdepth = 1
            and dependency.name in (select artifact_name from artifacts)
            -- We only need to lag over a short period because snapshots are duplicated
            -- data. Using 60 to ensure we capture the previous snapshot.
            and snapshotat between @start_date - interval 60 day and @end_date
    ),

    intermediate as (
        select
            time,
            case
                when previous_to_artifact_name is null
                then 'ADD_DEPENDENCY'
                when
                    to_artifact_name is not null
                    and to_artifact_name <> previous_to_artifact_name
                then 'REMOVE_DEPENDENCY'
                else 'NO_CHANGE'
            end as event_type,
            @event_source_name as event_source,
            @deps_parse_name(to_artifact_type, to_artifact_name) as to_artifact_name,
            @deps_parse_namespace(
                to_artifact_type, to_artifact_name
            ) as to_artifact_namespace,
            to_artifact_type,
            @deps_parse_name(
                from_artifact_type, from_artifact_name
            ) as from_artifact_name,
            @deps_parse_namespace(
                from_artifact_type, from_artifact_name
            ) as from_artifact_namespace,
            from_artifact_type,
            1.0 as amount
        from snapshots
    ),

    artifact_ids as (
        select
            time,
            event_type,
            event_source,
            @oso_id(
                event_source, to_artifact_namespace, to_artifact_name
            ) as to_artifact_id,
            to_artifact_name,
            to_artifact_namespace,
            to_artifact_type,
            @oso_id(event_source, to_artifact_type) as to_artifact_source_id,
            @oso_id(
                event_source, from_artifact_namespace, from_artifact_name
            ) as from_artifact_id,
            from_artifact_name,
            from_artifact_namespace,
            from_artifact_type,
            @oso_id(event_source, from_artifact_type) as from_artifact_source_id,
            amount
        from intermediate
        where event_type <> 'NO_CHANGE'
    ),

    changes as (
        select
            time,
            event_type,
            event_source,
            to_artifact_id,
            to_artifact_name,
            to_artifact_namespace,
            to_artifact_type,
            to_artifact_source_id,
            from_artifact_id,
            from_artifact_name,
            from_artifact_namespace,
            from_artifact_type,
            from_artifact_source_id,
            amount,
            @oso_id(
                event_source,
                time,
                to_artifact_id,
                to_artifact_type,
                from_artifact_id,
                from_artifact_type,
                event_type
            ) as event_source_id
        from artifact_ids
    )

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
from changes
