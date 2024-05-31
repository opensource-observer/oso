{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_deployer': ["root_deployer_address"],
    }
  }) 
}}

select distinct
  artifact_source,
  root_deployer_address,
  contract_address,
  contract_type
from {{ ref('int_contracts') }}
where root_deployer_address is not null
