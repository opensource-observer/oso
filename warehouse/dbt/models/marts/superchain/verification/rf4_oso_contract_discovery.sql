with projects as (
  select
    apps.application_id,
    apps.project_name,
    current_projects.blockchain
  from {{ source('static_data_sources', 'agora_rf4_applications') }} as apps
  left join
    {{ ref('stg_ossd__current_projects') }} as current_projects
    on apps.oso_project_name = current_projects.project_name
),

oso_blockchain_artifacts as (
  select
    projects.application_id,
    projects.project_name,
    'oso_verification' as discovery_method,
    UPPER(tag) as artifact_type,
    UPPER(network) as network,
    LOWER(JSON_VALUE(blockchains.address)) as address
  from projects
  cross join
    UNNEST(JSON_QUERY_ARRAY(projects.blockchain)) as blockchains
  cross join
    UNNEST(JSON_VALUE_ARRAY(blockchains.networks)) as network
  cross join
    UNNEST(JSON_VALUE_ARRAY(blockchains.tags)) as tag
  where tag in ('contract', 'deployer')
),

networks as (
  select *
  from UNNEST([
    struct('OPTIMISM' as network),
    struct('BASE' as network),
    struct('FRAX' as network),
    struct('METAL' as network),
    struct('MODE' as network),
    struct('ZORA' as network)
  ])
),

oso_any_evm_deployers as (
  select
    oso_blockchain_artifacts.application_id,
    oso_blockchain_artifacts.project_name,
    oso_blockchain_artifacts.artifact_type,
    networks.network,
    oso_blockchain_artifacts.address,
    oso_blockchain_artifacts.discovery_method
  from oso_blockchain_artifacts
  cross join networks
  where
    oso_blockchain_artifacts.artifact_type = 'DEPLOYER'
    and oso_blockchain_artifacts.network = 'ANY_EVM'
),

oso_other_addresses as (
  select
    application_id,
    project_name,
    artifact_type,
    network,
    address,
    discovery_method
  from oso_blockchain_artifacts
  where
    network in (select network from networks)
),

oso_addresses as (
  select *
  from oso_any_evm_deployers
  union all
  select *
  from oso_other_addresses
),

discovered_contracts as (
  select
    oso_addresses.application_id,
    oso_addresses.project_name,
    derived_contracts.contract_address as address,
    derived_contracts.network,
    --derived_contracts.factory_deployer_address,
    'CONTRACT' as artifact_type,
    'discovered_contract_from_oso_verified_deployer' as discovery_method
  from oso_addresses
  inner join {{ ref('int_derived_contracts') }} as derived_contracts
    on
      oso_addresses.address = derived_contracts.deployer_address
      and oso_addresses.network = derived_contracts.network
  where
    oso_addresses.address != derived_contracts.contract_address
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
from oso_addresses
