MODEL (
  name metrics.int_superchain_trace_level_events_by_project,
  description 'Events (down to trace level) involving known contracts with project-level attribution',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    event_type,
    project_id,
    from_artifact_id
  )
);

-- Step 1: Get joined traces and transactions
with base_transactions as (
  select
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx,
    to_address_trace,
    to_address_tx,
    gas_used_tx * gas_price_tx / 1e18 as gas_fee,
    @oso_id(chain, from_address_tx) as from_address_tx_id,
    @oso_id(chain, to_address_trace) as to_address_trace_id,
    @oso_id(chain, to_address_tx) as to_address_tx_id
  from metrics.int_superchain_traces_txs_joined
  where block_timestamp between @start_dt and @end_dt
),

-- Step 2: Precompute address-to-project mapping
addresses_by_project as (
  select distinct
    artifact_id,
    project_id
  from metrics.int_artifacts_by_project
),

-- Step 3: Compute transaction and trace events
transaction_level_events as (
  select distinct
    base_transactions.transaction_hash,
    abp.project_id,
    'TRANSACTION_EVENT' as event_type
  from base_transactions
  inner join addresses_by_project as abp
    on base_transactions.to_address_tx_id = abp.artifact_id
),

trace_level_events as (
  select distinct
    base_transactions.transaction_hash,
    abp.project_id,
    'TRACE_EVENT' as event_type
  from base_transactions
  inner join addresses_by_project as abp
    on base_transactions.to_address_trace_id = abp.artifact_id
),

-- Step 4: Combine transaction and trace events
all_contract_events as (
  select * from transaction_level_events
  union all
  select * from trace_level_events
),

-- Step 5: Count distinct projects per transaction and event type
events_per_project as (
  select
    transaction_hash,
    event_type,
    count(distinct project_id) as num_projects_per_event
  from all_contract_events
  group by
    transaction_hash,
    event_type
),

-- Step 6: Assign project counts back to each event
event_project_attribution as (
  select
    ace.transaction_hash,
    ace.project_id,
    ace.event_type,
    ep.num_projects_per_event
  from all_contract_events as ace
  inner join events_per_project as ep
    on ace.transaction_hash = ep.transaction_hash
    and ace.event_type = ep.event_type
),

-- Step 7: Extract other transaction metadata
transaction_metadata as (
  select distinct
    transaction_hash,
    chain,
    block_timestamp,
    from_address_tx_id as from_artifact_id,
    gas_fee
  from base_transactions
)

select
  tm.block_timestamp,
  tm.chain,
  epa.event_type,
  epa.project_id,
  epa.num_projects_per_event,
  tm.from_artifact_id,
  epa.transaction_hash,
  tm.gas_fee
from event_project_attribution as epa
inner join transaction_metadata as tm
  on epa.transaction_hash = tm.transaction_hash