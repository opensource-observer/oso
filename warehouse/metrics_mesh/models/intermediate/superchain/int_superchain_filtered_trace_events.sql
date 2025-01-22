MODEL (
  name metrics.int_superchain_filtered_trace_events,
  kind FULL,
);

with events as (
  select
    @from_unix_timestamp(block_timestamp) as "time",
    event_source,
    transaction_hash,
    from_address_tx,
    from_address_trace,
    to_address_trace,
    to_address_tx,
    gas,
    gas_used_trace,
    gas_price,
    @oso_id('event_source', 'from_address_tx') as from_address_tx_id,
    @oso_id('event_source', 'from_address_trace') as from_address_trace_id,
    @oso_id('event_source', 'to_address_trace') as to_address_trace_id,
    @oso_id('event_source', 'to_address_tx') as to_address_tx_id
  from metrics.stg_superchain__traces_joined
),

known_contracts as (
  select distinct artifact_id
  from metrics.int_artifacts_by_project
  where artifact_id not in (
    select artifact_id
    from metrics.int_artifacts_in_ossd_by_project
    where artifact_type = 'WALLET'
  )
),

bot_filtered_events as (
  select * from events
  left join @oso_source('bigquery.oso.int_superchain_potential_bots') as bots
    on events.from_address_tx_id = bots.artifact_id
  where bots.artifact_id is null
),

filtered_traces as (
  select bot_filtered_events.*
  from bot_filtered_events
  inner join known_contracts
    on bot_filtered_events.to_address_trace_id = known_contracts.artifact_id
),

filtered_txns as (
  select distinct
    "time",
    event_source,
    transaction_hash,
    from_address_tx_id,
    to_address_tx_id,
    gas,
    gas_price
  from bot_filtered_events
  inner join known_contracts
    on bot_filtered_events.to_address_tx_id = known_contracts.artifact_id
),

trace_counts as (
  select
    date_trunc('DAY', time::DATE) as "time",
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
    date_trunc("time", day) as "time",
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
    date_trunc('DAY', "time"::DATE) as "time",
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
    date_trunc('DAY', "time"::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_tx_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_L2_GAS_USED' as event_type,
    sum(gas) as amount
  from filtered_txns
  group by 1, 2, 3, 4
),

txn_gas_fees as (
  select
    date_trunc('DAY', "time"::DATE) as "time",
    event_source,
    from_address_tx_id as from_artifact_id,
    to_address_tx_id as to_artifact_id,
    'CONTRACT_INVOCATION_SUCCESS_DAILY_L2_GAS_FEES' as event_type,
    sum(gas_price * gas) / 1e18 as amount
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