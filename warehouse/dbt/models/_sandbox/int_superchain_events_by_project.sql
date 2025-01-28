{{
  config(
    materialized='table'
  )
}}

with events as (
  select
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx,
    from_address_trace,
    to_address_trace,
    to_address_tx,
    gas_used_tx,
    gas_used_trace,
    gas_price_tx,
    {{ oso_id("chain", "from_address_tx") }} as from_address_tx_id,
    {{ oso_id("chain", "from_address_trace") }} as from_address_trace_id,
    {{ oso_id("chain", "to_address_trace") }} as to_address_trace_id,
    {{ oso_id("chain", "to_address_tx") }} as to_address_tx_id
  from {{ ref('int_superchain_traces_txs_joined') }}
),

addresses_by_project as (
  select distinct
    artifact_id,
    project_id,
    project_name
  from {{ ref('int_artifacts_by_project') }}
),

filtered_txns as (
  select distinct
    addresses_by_project.project_id as to_project_id,
    events.block_timestamp,
    events.chain,
    events.transaction_hash,
    events.from_address_tx_id as from_artifact_id,
    events.to_address_tx_id as to_artifact_id,
    events.gas_used_tx as gas_used,
    events.gas_price_tx as gas_price,
    'TRANSACTION_EVENT' as event_type
  from events
  inner join addresses_by_project
    on events.to_address_tx_id = addresses_by_project.artifact_id
),

filtered_traces as (
  select distinct
    addresses_by_project.project_id as to_project_id,
    events.block_timestamp,
    events.chain,
    events.transaction_hash,
    events.from_address_tx_id as from_artifact_id,
    events.to_address_trace_id as to_artifact_id,
    events.gas_used_trace as gas_used,
    events.gas_price_tx as gas_price,
    'TRACE_EVENT' as event_type
  from events
  inner join addresses_by_project
    on events.to_address_trace_id = addresses_by_project.artifact_id
  where events.to_address_trace_id != events.to_address_tx_id
),


union_events as (
  select * from filtered_traces
  union all
  select * from filtered_txns
)

select * from union_events
