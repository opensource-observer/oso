MODEL (
  name metrics.int_events__dependencies,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

@DEF(event_source_name, 'DEPS_DEV');

with artifacts as (
  select artifact_name
  from metrics.int_all_artifacts
  where artifact_source = 'NPM'
),

snapshots as (
  select
    SnapshotAt as time,
    System as from_artifact_type,
    Name as from_artifact_name,
    Version as from_artifact_version,
    Dependency.Name as to_artifact_name,
    Dependency.System as to_artifact_type,
    Dependency.Version as to_artifact_version,
    LAG(Dependency.Name) over (
      partition by System, Name, Dependency.Name, Version, Dependency.Version
      order by SnapshotAt
    ) as previous_to_artifact_name
  from @oso_source('bigquery.oso.stg_deps_dev__dependencies')
  where
    MinimumDepth = 1
    and Dependency.Name in (select artifact_name from artifacts)
    -- We only need to lag over a short period because snapshots are duplicated
    -- data. Using 60 to ensure we capture the previous snapshot.
    and SnapshotAt between @start_date - INTERVAL 60 DAY and @end_date
),

intermediate as (
  select
    time,
    case
      when previous_to_artifact_name is null then 'ADD_DEPENDENCY'
      when
        to_artifact_name is not null and to_artifact_name <> previous_to_artifact_name
        then 'REMOVE_DEPENDENCY'
      else 'NO_CHANGE'
    end as event_type,
    @event_source_name as event_source,
    @deps_parse_name(to_artifact_type, to_artifact_name) as to_artifact_name,
    @deps_parse_namespace(to_artifact_type, to_artifact_name) as to_artifact_namespace,
    to_artifact_type,
    @deps_parse_name(from_artifact_type, from_artifact_name) as from_artifact_name,
    @deps_parse_namespace(from_artifact_type, from_artifact_name) as from_artifact_namespace,
    from_artifact_type,
    1.0 as amount
  from snapshots
),

artifact_ids as (
  select
    time,
    event_type,
    event_source,
    @oso_id(event_source, to_artifact_namespace, to_artifact_name) as to_artifact_id,
    to_artifact_name,
    to_artifact_namespace,
    to_artifact_type,
    @oso_id(event_source, to_artifact_type) as to_artifact_source_id,
    @oso_id(event_source, from_artifact_namespace, from_artifact_name) as from_artifact_id,
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
  UPPER(event_type) as event_type,
  CAST(event_source_id as STRING) as event_source_id,
  UPPER(event_source) as event_source,
  LOWER(to_artifact_name) as to_artifact_name,
  LOWER(to_artifact_namespace) as to_artifact_namespace,
  UPPER(to_artifact_type) as to_artifact_type,
  LOWER(to_artifact_source_id) as to_artifact_source_id,
  LOWER(from_artifact_name) as from_artifact_name,
  LOWER(from_artifact_namespace) as from_artifact_namespace,
  UPPER(from_artifact_type) as from_artifact_type,
  LOWER(from_artifact_source_id) as from_artifact_source_id,
  CAST(amount as DOUBLE) as amount
from changes
