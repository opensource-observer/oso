select
  dt as block_timestamp,
  `hash` as transaction_hash,
  from_address,
  to_address,
  gas as gas_used,
  gas_price,
  upper(
    case
      when chain = 'op' then 'optimism'
      when chain = 'fraxtal' then 'frax'
      else chain
    end
  ) as chain
from {{ source('optimism_superchain_raw_onchain_data', 'transactions') }}
where
  dt >= '2024-11-01'
  and network = 'mainnet'
  and receipt_status = 1
  and gas > 0