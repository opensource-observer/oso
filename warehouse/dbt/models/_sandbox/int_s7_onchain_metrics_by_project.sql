{{
  config(
    materialized='table'
  )
}}

{% set gas_cap = 0.03 / 3000 * 1e18 %}

with filtered_events as (
  select *
  from {{ ref('int_superchain_events_by_project') }} e
  where from_artifact_id not in (
    select artifact_id
    from {{ ref('int_superchain_potential_bots') }} b
  )
),

-- Calculate base gas fees per transaction
transaction_gas_fees as (
  select
    transaction_hash,
    chain,
    timestamp_trunc(block_timestamp, month) as sample_date,
    sum(gas_used * gas_price) as total_gas_fee,
    least(sum(gas_used * gas_price), {{ gas_cap }}) as capped_gas_fee
  from filtered_events
  group by 1, 2, 3
),

-- Calculate weights and gas fees for both transaction and trace events
event_weights as (
  select
    e.transaction_hash,
    e.chain,
    timestamp_trunc(e.block_timestamp, month) as sample_date,
    e.to_project_id,
    e.event_type,
    e.gas_used * e.gas_price as event_gas_fee,
    g.total_gas_fee,
    g.capped_gas_fee,
    -- Calculate weights based on event type
    case 
      when e.event_type = 'TRANSACTION_EVENT' then 0.5
      when e.event_type = 'TRACE_EVENT' then 
        0.5 / nullif(sum(case when e.event_type = 'TRACE_EVENT' then 1 else 0 end) 
          over (partition by e.transaction_hash), 0)
    end as weight,
    -- Calculate pro-rata share for capped gas fees
    case
      when e.event_type = 'TRANSACTION_EVENT' then 
        least(e.gas_used * e.gas_price * 0.5, g.capped_gas_fee * 0.5)
      when e.event_type = 'TRACE_EVENT' then
        (g.capped_gas_fee * 0.5 * (e.gas_used * e.gas_price)) / 
        nullif(sum(case when e.event_type = 'TRACE_EVENT' then e.gas_used * e.gas_price else 0 end) 
          over (partition by e.transaction_hash), 0)
    end as capped_weight
  from filtered_events e
  left join transaction_gas_fees g
    on e.transaction_hash = g.transaction_hash
),

-- Transaction counts (non-amortized)
transaction_counts as (
  select 
    to_project_id as project_id,
    chain,
    timestamp_trunc(block_timestamp, month) as sample_date,
    count(distinct transaction_hash) as amount
  from filtered_events
  where event_type = 'TRANSACTION_EVENT'
  group by 1, 2, 3
),

-- Trace counts
trace_counts as (
  select 
    to_project_id as project_id,
    chain,
    timestamp_trunc(block_timestamp, month) as sample_date,
    count(distinct transaction_hash) as amount
  from filtered_events
  where event_type = 'TRACE_EVENT'
  group by 1, 2, 3
),

-- Amortized transaction counts
amortized_counts as (
  select
    to_project_id as project_id,
    chain,
    sample_date,
    sum(weight) as amount
  from event_weights
  group by 1, 2, 3
),

-- Transaction gas fees (uncapped)
transaction_gas as (
  select
    to_project_id as project_id,
    chain,
    sample_date,
    sum(event_gas_fee) / 1e18 as amount
  from event_weights
  where event_type = 'TRANSACTION_EVENT'
  group by 1, 2, 3
),

-- Trace gas fees (uncapped)
trace_gas as (
  select
    to_project_id as project_id,
    chain,
    sample_date,
    sum(event_gas_fee) / 1e18 as amount
  from event_weights
  where event_type = 'TRACE_EVENT'
  group by 1, 2, 3
),

-- Amortized gas fees (uncapped)
amortized_gas as (
  select
    to_project_id as project_id,
    chain,
    sample_date,
    sum(event_gas_fee * weight) / 1e18 as amount
  from event_weights
  group by 1, 2, 3
),

-- Transaction gas fees (capped)
transaction_gas_capped as (
  select
    to_project_id as project_id,
    chain,
    sample_date,
    sum(capped_weight) / 1e18 as amount
  from event_weights
  where event_type = 'TRANSACTION_EVENT'
  group by 1, 2, 3
),

-- Amortized gas fees (capped)
amortized_gas_capped as (
  select
    to_project_id as project_id,
    chain,
    sample_date,
    sum(capped_weight) / 1e18 as amount
  from event_weights
  group by 1, 2, 3
),

monthly_active_farcaster_users as (
  select
    filtered_events.to_project_id as project_id,
    filtered_events.chain,
    timestamp_trunc(filtered_events.block_timestamp, month) as sample_date,
    count(distinct users.user_source_id) as amount
  from filtered_events
  inner join {{ ref('int_users') }} as users
    on filtered_events.from_artifact_id = users.user_id
  where users.user_source = 'FARCASTER'
  group by 1, 2, 3
),

monthly_active_addresses as (
  select
    to_project_id as project_id,
    chain,
    timestamp_trunc(block_timestamp, month) as sample_date,
    count(distinct from_artifact_id) as amount
  from filtered_events
  group by 1, 2, 3
),

-- Union all metrics together
metrics_combined as (
  select 
    project_id,
    chain,
    sample_date,
    'transaction_count' as metric_name,
    amount
  from transaction_counts

  union all

  select 
    project_id,
    chain,
    sample_date,
    'trace_count' as metric_name,
    amount
  from trace_counts

  union all

  select 
    project_id,
    chain,
    sample_date,
    'amortized_transaction_count' as metric_name,
    amount
  from amortized_counts

  union all

  select 
    project_id,
    chain,
    sample_date,
    'transaction_gas_fees' as metric_name,
    amount
  from transaction_gas

  union all

  select 
    project_id,
    chain,
    sample_date,
    'trace_gas_fees' as metric_name,
    amount
  from trace_gas

  union all

  select 
    project_id,
    chain,
    sample_date,
    'amortized_gas_fees' as metric_name,
    amount
  from amortized_gas

  union all

  select 
    project_id,
    chain,
    sample_date,
    'transaction_gas_fees_capped' as metric_name,
    amount
  from transaction_gas_capped

  union all

  select 
    project_id,
    chain,
    sample_date,
    'amortized_gas_fees_capped' as metric_name,
    amount
  from amortized_gas_capped

  union all

  select 
    project_id,
    chain,
    sample_date,
    'monthly_active_farcaster_users' as metric_name,
    amount
  from monthly_active_farcaster_users

  union all

  select 
    project_id,
    chain,
    sample_date,
    'monthly_active_addresses' as metric_name,
    amount
  from monthly_active_addresses
)

select
  project_id,
  chain,
  sample_date,
  metric_name,
  amount
from metrics_combined
where project_id is not null
