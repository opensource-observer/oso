{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_deployer': ["root_deployer_address"],
    }
  }) 
}}

select distinct
  network as artifact_source,
  deployer_address as root_deployer_address,
  contract_address
from {{ ref('int_derived_contracts') }}
