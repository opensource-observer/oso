with deployers as (
  select
    *,
    'OPTIMISM' as chain
  from {{ ref('stg_optimism__deployers') }}
  union all
  select
    *,
    'BASE' as chain
  from {{ ref('stg_base__deployers') }}
  union all
  select
    *,
    'FRAX' as chain
  from {{ ref('stg_frax__deployers') }}
  union all
  select
    *,
    'MODE' as chain
  from {{ ref('stg_mode__deployers') }}
  union all
  select
    *,
    'ZORA' as chain
  from {{ ref('stg_zora__deployers') }}
)

select
  block_timestamp,
  transaction_hash,
  chain as deployer_source,
  deployer_address,
  contract_address
from deployers
order by block_timestamp desc
