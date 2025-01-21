{{
  config(
    materialized='table',
    partition_by={
      "field": "time",
      "data_type": "timestamp",
      "granularity": "day",
    },
    meta={
      'sync_to_db': False
    }
  )
}}

with open_collective_expenses as (
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
    CAST(amount as FLOAT64) as amount
  from {{ open_collective_events("stg_open_collective__expenses") }}
),

open_collective_deposits as (
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
    CAST(amount as FLOAT64) as amount
  from {{ open_collective_events("stg_open_collective__deposits") }}
)

select * from open_collective_expenses
union all
select * from open_collective_deposits
