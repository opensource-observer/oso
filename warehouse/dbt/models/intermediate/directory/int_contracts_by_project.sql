with contracts_in_ossd as (
  select distinct
    project_id,
    artifact_source as network,
    artifact_name as contract_address
  from {{ ref('int_artifacts_in_ossd_by_project') }}
  where artifact_type in ('CONTRACT', 'FACTORY')
),

deployers_by_project as (
  select
    project_id,
    artifact_source as network,
    artifact_name as deployer_address
  from {{ ref('int_deployers_by_project') }}
),

derived_contracts as (
  select
    network,
    deployer_address,
    contract_address
  from {{ ref('int_derived_contracts') }}
),

derived_contracts_by_project as (
  select
    deployers_by_project.project_id,
    derived_contracts.network,
    derived_contracts.contract_address
  from derived_contracts
  left join deployers_by_project
    on
      derived_contracts.deployer_address = deployers_by_project.deployer_address
      and derived_contracts.network = deployers_by_project.network
  where deployers_by_project.deployer_address is not null
),

unified_contracts as (
  select distinct *
  from (
    select
      project_id,
      network,
      contract_address
    from contracts_in_ossd
    union all
    select
      project_id,
      network,
      contract_address
    from derived_contracts_by_project
  )
),

factories as (
  select
    network,
    factory_address,
    contract_address
  from {{ ref('int_factories') }}
),

discovered_contracts as (
  select
    unified_contracts.project_id,
    unified_contracts.network,
    factories.contract_address
  from factories
  left join unified_contracts
    on
      factories.factory_address = unified_contracts.contract_address
      and factories.network = unified_contracts.network
  where unified_contracts.project_id is not null
),

contracts_by_project as (
  select distinct *
  from (
    select
      project_id,
      network,
      contract_address
    from discovered_contracts
    union all
    select
      project_id,
      network,
      contract_address
    from unified_contracts
  )
)

select
  project_id,
  {{ oso_id("network", "contract_address") }} as artifact_id,
  network as artifact_source,
  contract_address as artifact_source_id,
  LOWER(network) as artifact_namespace,
  contract_address as artifact_name
from contracts_by_project
