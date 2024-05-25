{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  artifact_source as network,
  root_deployer_address,
  contract_address,
  contract_type
from {{ ref('int_contracts') }}
where root_deployer_address is not null
