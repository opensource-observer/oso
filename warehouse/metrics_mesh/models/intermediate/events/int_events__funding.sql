MODEL (
  name metrics.int_events__funding,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

with open_collective_expenses as (
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
    from metrics.stg_open_collective__expenses
    where unit = 'USD'
      and time between @start_dt and @end_dt
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
    from metrics.stg_open_collective__deposits
    where unit = 'USD'
      and time between @start_dt and @end_dt
),

all_funding_events as (
    select * from open_collective_expenses
    union all
    select * from open_collective_deposits
)

select
    time,
    to_artifact_id,
    from_artifact_id,
    UPPER(event_type) as event_type,
    CAST(event_source_id as STRING) as event_source_id,
    UPPER(event_source) as event_source,
    LOWER(to_name) as to_artifact_name,
    LOWER(to_namespace) as to_artifact_namespace,
    UPPER(to_type) as to_artifact_type,
    LOWER(to_artifact_source_id) as to_artifact_source_id,
    LOWER(from_name) as from_artifact_name,
    LOWER(from_namespace) as from_artifact_namespace,
    UPPER(from_type) as from_artifact_type,
    LOWER(from_artifact_source_id) as from_artifact_source_id,
    CAST(amount as DOUBLE) as amount
from all_funding_events
