with contracts as (
  select
    application_id,
    project_name,
    address,
    network,
    artifact_type,
    discovery_method
  from {{ ref('rf4_oso_contract_discovery') }}
  where artifact_type = 'CONTRACT'
  union all
  select
    application_id,
    project_name,
    address,
    network,
    artifact_type,
    discovery_method
  from {{ ref('rf4_agora_contract_discovery') }}
  where artifact_type = 'CONTRACT'
)

select distinct
  application_id,
  address as contract_address,
  network,
  discovery_method
from contracts
where application_id is not null
