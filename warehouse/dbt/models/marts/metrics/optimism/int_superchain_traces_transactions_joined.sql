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
  select * from {{ ref('stg_superchain__traces') }}
),

transactions as (
  select * from {{ ref('stg_superchain__transactions') }}
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
