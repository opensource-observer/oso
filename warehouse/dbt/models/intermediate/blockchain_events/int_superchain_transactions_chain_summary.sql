{{
  config(
    materialized='table',
    meta={
      'sync_to_db': False
    }
  )
}}

select
  dt,
  from_address,
  to_address,
  chain,
  sum(cast(value_64 as numeric)) as total_transferred,
  sum(gas * gas_price / 1e18) as total_gas_fee
from {{ source('optimism_superchain_raw_onchain_data', 'transactions') }}
where
  dt >= '2024-06-01'
  and receipt_status = 1
  and network = 'mainnet'
  and to_address != ''
  and from_address != ''
  and chain in (
    'op',
    'cyber',
    'fraxtal',
    'kroma',
    'mode',
    'mint',
    'swan',
    'lyra',
    'lisk'
  )
group by
  dt,
  from_address,
  to_address,
  chain
