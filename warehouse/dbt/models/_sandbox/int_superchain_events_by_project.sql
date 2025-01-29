{{
  config(
    materialized='table',
    partition_by={
      "field": "block_timestamp",
      "data_type": "date",
      "granularity": "day",
    }
  )
}}

-- Step 1: Join traces and transactions
with txs as (
  select
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx,
    to_address_trace,
    to_address_tx,
    gas_used_tx * gas_price_tx / 1e18 as gas_fee,
    {{ oso_id("chain", "from_address_tx") }} as from_address_tx_id,
    {{ oso_id("chain", "to_address_trace") }} as to_address_trace_id,
    {{ oso_id("chain", "to_address_tx") }} as to_address_tx_id
  from {{ ref('int_superchain_traces_txs_joined') }}
),

-- Step 2: Precompute address-to-project mapping
addresses_by_project as (
  select distinct
    artifact_id,
    project_id
  from {{ ref('int_artifacts_by_project') }}
),

-- Step 3: Compute transaction and trace events
tx_events as (
  select distinct
    txs.transaction_hash,
    abp.project_id,
    'TRANSACTION_EVENT' as event_type
  from txs
  inner join addresses_by_project as abp
    on txs.to_address_tx_id = abp.artifact_id
),

trace_events as (
  select distinct
    txs.transaction_hash,
    abp.project_id,
    'TRACE_EVENT' as event_type
  from txs
  inner join addresses_by_project as abp
    on txs.to_address_trace_id = abp.artifact_id
),

-- Step 4: Combine transaction and trace events
unioned_events as (
  select * from tx_events
  union all
  select * from trace_events
),

-- Step 5: Count distinct projects per transaction and event type
project_counts as (
  select
    transaction_hash,
    event_type,
    count(distinct project_id) as num_distinct_projects
  from unioned_events
  group by
    transaction_hash,
    event_type
),

-- Step 6: Assign project weights
project_weights as (
  select
    ue.transaction_hash,
    ue.project_id,
    ue.event_type,
    case
      when ue.event_type = 'TRANSACTION_EVENT'
        then 0.5 / nullif(pc.num_distinct_projects, 0)
      when ue.event_type = 'TRACE_EVENT'
        then 0.5 / nullif(pc.num_distinct_projects, 0)
    end as project_weight
  from unioned_events as ue
  inner join project_counts as pc
    on
      ue.transaction_hash = pc.transaction_hash
      and ue.event_type = pc.event_type
),

-- Step 7: Extract other transaction metadata
other_tx_data as (
  select distinct
    transaction_hash,
    chain,
    block_timestamp,
    from_address_tx_id as from_artifact_id,
    gas_fee
  from txs
)

select
  pw.transaction_hash,
  pw.event_type,
  pw.project_id,
  pw.project_weight,
  otx.chain,
  otx.block_timestamp,
  otx.from_artifact_id,
  otx.gas_fee
from project_weights as pw
inner join other_tx_data as otx
  on pw.transaction_hash = otx.transaction_hash
