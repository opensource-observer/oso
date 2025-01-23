{{
  config(
    materialized='incremental',
    partition_by={
      "field": "time",
      "data_type": "date",
      "granularity": "day",
    }
  )
}}


with traces as (
  select
    dt,
    chain,
    gas_used,
    transaction_hash,
    from_address,
    to_address
  from {{ source('optimism_superchain_raw_onchain_data', 'traces') }}
  where
    dt >= '2024-11-01'
    and network = 'mainnet'
    and `status` = 1
    and call_type in ('delegatecall', 'call')
),

transactions as (
  select
    dt,
    chain,
    gas,
    gas_price,
    `hash` as transaction_hash,
    from_address,
    to_address
  from {{ source('optimism_superchain_raw_onchain_data', 'transactions') }}
  where
    dt >= '2024-11-01'
    and network = 'mainnet'
    and receipt_status = 1
)

select
  transactions.dt as `time`,
  transactions.transaction_hash,
  transactions.from_address as from_address_tx,
  traces.from_address as from_address_trace,
  traces.to_address as to_address_trace,
  transactions.to_address as to_address_tx,
  transactions.gas as gas,
  traces.gas_used as gas_used_trace,
  transactions.gas_price as gas_price,
  upper(
    case
      when transactions.chain = 'op' then 'optimism'
      when transactions.chain = 'fraxtal' then 'frax'
      else transactions.chain
    end
  ) as event_source
from transactions
left join traces
  on
    transactions.transaction_hash = traces.transaction_hash
    and transactions.chain = traces.chain
