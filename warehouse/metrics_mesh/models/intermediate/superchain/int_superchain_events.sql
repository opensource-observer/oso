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
  partitioned_by (DAY("time"), "event_source"),
  grain (
    "time",
    event_source,
    from_artifact_id,
    to_artifact_id,
    event_type
  )
);

with events as (
  select
    block_timestamp, 
    chain as event_source,
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

filtered_traces as (
  select distinct
    events.block_timestamp,
    events.event_source,
    events.transaction_hash,
    events.from_address_tx_id,
    events.to_address_trace_id,
    events.gas_used_trace
  from events
  inner join metrics.int_artifacts_by_project as known_addresses
    on events.to_address_trace_id = known_addresses.artifact_id
),

filtered_txns as (
  select distinct
    events.block_timestamp,
    events.event_source,
    events.transaction_hash,
    events.from_address_tx_id,
    events.to_address_tx_id,
    events.gas_used_tx,
    events.gas_price
  from events
  inner join metrics.int_artifacts_by_project as known_addresses
    on events.to_address_tx_id = known_addresses.artifact_id
),

trace_counts as (
  select
    date_trunc('DAY', block_timestamp::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_trace_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_TRACE_COUNT' as event_type,
    count(distinct transaction_hash) as amount
  from filtered_traces
  group by 1, 2, 3, 4
),

trace_gas_used as (
  select
    date_trunc('DAY', block_timestamp::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_trace_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_TRACE_L2_GAS_USED' as event_type,
    sum(gas_used_trace) as amount
  from filtered_traces
  group by 1, 2, 3, 4
),

txn_counts as (
  select
    date_trunc('DAY', block_timestamp::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_tx_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT' as event_type,
    count(distinct transaction_hash) as amount
  from filtered_txns
  group by 1, 2, 3, 4
),

txn_gas_used as (
  select
    date_trunc('DAY', block_timestamp::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_tx_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_L2_GAS_USED' as event_type,
    sum(gas_used_tx) as amount
  from filtered_txns
  group by 1, 2, 3, 4
),

txn_gas_fees as (
  select
    date_trunc('DAY', block_timestamp::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_tx_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_L2_GAS_FEES' as event_type,
    sum(gas_price * gas_used_tx) / 1e18 as amount
  from filtered_txns
  group by 1, 2, 3, 4
)

select * from trace_counts
union all
select * from trace_gas_used
union all
select * from txn_counts
union all
select * from txn_gas_used
union all
select * from txn_gas_fees