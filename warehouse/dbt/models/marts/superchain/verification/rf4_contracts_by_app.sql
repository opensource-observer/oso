with factories as (
  select
    factory_address,
    contract_address,
    network
  from {{ ref('int_factories') }}
),

app_contracts as (
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
),

discovered_contracts as (
  select
    app_contracts.application_id,
    app_contracts.project_name,
    factories.contract_address as address,
    factories.network,
    'CONTRACT' as artifact_type,
    'discovered_contract_from_verified_factory' as discovery_method
  from factories
  left join app_contracts
    on
      factories.factory_address = app_contracts.address
      and factories.network = app_contracts.network
),

contracts as (
  select
    application_id,
    address,
    network,
    discovery_method
  from discovered_contracts
  union all
  select
    application_id,
    address,
    network,
    discovery_method
  from app_contracts
)

select distinct
  application_id,
  address as contract_address,
  network,
  discovery_method
from contracts
where application_id is not null
