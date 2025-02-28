MODEL (
  name metrics.int_contracts_by_project,
  kind FULL,
);

with contracts_in_ossd as (
  select
    project_id,
    artifact_source as chain,
    artifact_name as contract_address
  from metrics.int_artifacts_by_project_in_ossd
  where artifact_type = 'CONTRACT'
),

derived_contracts_by_project as (
  select
    deployers_by_project.project_id,
    derived_contracts.chain,
    derived_contracts.contract_address
  from metrics.int_derived_contracts as derived_contracts
  left join metrics.int_deployers_by_project as deployers_by_project
    on
      derived_contracts.originating_address = deployers_by_project.artifact_name
      and derived_contracts.chain = deployers_by_project.artifact_source
  where deployers_by_project.artifact_name is not null
),

unified_contracts as (
  select distinct *
  from (
    select
      project_id,
      chain,
      contract_address
    from contracts_in_ossd
    union all
    select
      project_id,
      chain,
      contract_address
    from derived_contracts_by_project
  )
),

discovered_contracts as (
  select
    unified_contracts.project_id,
    unified_contracts.chain,
    factories.contract_address
  from metrics.int_factories as factories
  left join unified_contracts
    on
      factories.factory_address = unified_contracts.contract_address
      and factories.chain = unified_contracts.chain
  where unified_contracts.project_id is not null
),

contracts_by_project as (
  select distinct *
  from (
    select
      project_id,
      chain,
      contract_address
    from discovered_contracts
    union all
    select
      project_id,
      chain,
      contract_address
    from unified_contracts
  )
)

select
  project_id,
  @oso_id(chain, contract_address) as artifact_id,
  chain as artifact_source,
  contract_address as artifact_source_id,
  LOWER(chain) as artifact_namespace,
  contract_address as artifact_name
from contracts_by_project
