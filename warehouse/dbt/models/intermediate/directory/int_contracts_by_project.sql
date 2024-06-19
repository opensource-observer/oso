with contracts as (
  select
    block_timestamp,
    transaction_hash,
    network,
    deployer_address,
    contract_address
  from {{ ref('int_derived_contracts') }}
),

deployers as (
  select
    project_id,
    artifact_name as deployer_address,
    artifact_source as network
  from {{ ref('int_deployers_by_project') }}
),

discovered_contracts as (
  select
    deployers.project_id,
    contracts.block_timestamp,
    contracts.transaction_hash,
    contracts.network,
    contracts.deployer_address,
    contracts.contract_address
  from contracts
  left join deployers
    on
      contracts.deployer_address = deployers.deployer_address
      and contracts.network = deployers.network
  where deployers.deployer_address is not null
)

select
  project_id,
  {{ oso_id("network", "contract_address") }} as artifact_id,
  network as artifact_source,
  contract_address as artifact_source_id,
  LOWER(network) as artifact_namespace,
  contract_address as artifact_name
from discovered_contracts
