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

with all_events as (
  select
    time,
    event_type,
    event_source_id,
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
    amount
  from (
    select * from {{ ref('int_optimism_contract_invocation_events') }}
    union all
    select * from {{ ref('int_base_contract_invocation_events') }}
    union all
    select * from {{ ref('int_frax_contract_invocation_events') }}
    union all
    select * from {{ ref('int_metal_contract_invocation_events') }}
    union all
    select * from {{ ref('int_mode_contract_invocation_events') }}
    union all
    select * from {{ ref('int_pgn_contract_invocation_events') }}
    union all
    select * from {{ ref('int_zora_contract_invocation_events') }}
    union all
    select * from {{ ref('int_arbitrum_one_contract_invocation_events') }}
  )
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
  CAST(amount as FLOAT64) as amount
from all_events
