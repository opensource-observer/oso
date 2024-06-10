with agora as (
  select
    application_id,
    project_name,
    artifact as address,
    artifact_source as network,
    artifact_type,
    'agora_verification' as discovery_method
  from {{ source('static_data_sources', 'agora_rf4_artifacts_by_app') }}
  where artifact_type in ('CONTRACT', 'DEPLOYER')
),

discovered_contracts as (
  select
    agora.application_id,
    agora.project_name,
    derived_contracts.contract_address as address,
    derived_contracts.network,
    --derived_contracts.factory_deployer_address,
    'CONTRACT' as artifact_type,
    'discovered_contract_from_agora_verified_deployer' as discovery_method
  from agora
  inner join {{ ref('int_derived_contracts') }} as derived_contracts
    on
      agora.address = derived_contracts.deployer_address
      and agora.network = derived_contracts.network
  where
    agora.address != derived_contracts.contract_address
)

select
  application_id,
  project_name,
  address,
  network,
  artifact_type,
  discovery_method
from discovered_contracts
union all
select
  application_id,
  project_name,
  address,
  network,
  artifact_type,
  discovery_method
from agora
