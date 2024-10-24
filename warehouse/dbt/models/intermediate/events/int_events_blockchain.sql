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
