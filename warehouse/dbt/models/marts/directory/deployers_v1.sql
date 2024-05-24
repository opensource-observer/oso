{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  block_timestamp,
  transaction_hash,
  deployer_source,
  deployer_address,
  contract_address
from {{ ref('int_deployers') }}
