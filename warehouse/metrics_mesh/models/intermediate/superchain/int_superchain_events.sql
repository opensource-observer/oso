MODEL (
  name metrics.int_superchain_events,
  description 'Events (transactions, traces, gas, etc.) involving known contracts',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column "time",
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "chain"),
  grain (
    "time",
    project_id,
    chain,
    transaction_hash,
    from_artifact_id,
    to_artifact_id,
    event_type
  )
);

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
    gas_price,
    @oso_id('chain', 'from_address_tx') as from_address_tx_id,
    @oso_id('chain', 'from_address_trace') as from_address_trace_id,
    @oso_id('chain', 'to_address_trace') as to_address_trace_id,
    @oso_id('chain', 'to_address_tx') as to_address_tx_id
  from metrics.int_superchain_traces_txs_joined
  where block_timestamp between @start_dt and @end_dt
),

addresses_by_project as(
  select distinct
    artifact_id,
    project_id,
    project_name
  from metrics.int_artifacts_by_project
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
    events.gas_price as gas_price,
    'TRACE_EVENT' as event_type
  from events
  inner join addresses_by_project
    on events.to_address_trace_id = addresses_by_project.artifact_id
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
    events.gas_price as gas_price,
    'TRANSACTION_EVENT' as event_type
  from events
  inner join addresses_by_project
    on events.to_address_tx_id = addresses_by_project.artifact_id
),

filtered_4337_from_events as (
  select distinct
    addresses_by_project.project_id as to_project_id,
    events.block_timestamp,
    events.chain,
    events.transaction_hash,
    events.from_address_tx_id as from_artifact_id,
    events.to_address_trace_id as to_artifact_id,
    events.gas_used_trace as gas_used,
    events.gas_price as gas_price,
    '4337_FROM_EVENT' as event_type
  from events
  inner join addresses_by_project
    on events.from_address_trace_id = addresses_by_project.artifact_id
  where addresses_by_project.project_name = 'eth-infinitism-account-abstraction'
),

filtered_4337_to_events as (
  select distinct
    addresses_by_project.project_id as to_project_id,
    events.block_timestamp,
    events.chain,
    events.transaction_hash,
    events.from_address_tx_id as from_artifact_id,
    events.to_address_tx_id as to_artifact_id,
    events.gas_used_tx as gas_used,
    events.gas_price as gas_price,
    '4337_TO_EVENT' as event_type
  from events
  inner join addresses_by_project
    on events.to_address_tx_id = addresses_by_project.artifact_id
  where addresses_by_project.project_name = 'eth-infinitism-account-abstraction'
),


union_events as (
  select * from filtered_traces
  union all
  select * from filtered_txns
  union all
  select * from filtered_4337_from_events
  union all
  select * from filtered_4337_to_events
)

select * from union_events
