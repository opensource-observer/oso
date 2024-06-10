{#
  TODO: This needs to be refactored or deprecated.
#}

with deployers as (
  select
    *,
    'OPTIMISM' as artifact_source
  from {{ ref('stg_optimism__deployers') }}
  union all
  select
    *,
    'BASE' as artifact_source
  from {{ ref('stg_base__deployers') }}
  union all
  select
    *,
    'FRAX' as artifact_source
  from {{ ref('stg_frax__deployers') }}
  union all
  select
    *,
    'METAL' as artifact_source
  from {{ ref('stg_metal__deployers') }}
  union all
  select
    *,
    'MODE' as artifact_source
  from {{ ref('stg_mode__deployers') }}
  union all
  select
    *,
    'ZORA' as artifact_source
  from {{ ref('stg_zora__deployers') }}
),

factories as (
  select
    *,
    'OPTIMISM' as artifact_source
  from {{ ref('stg_optimism__factories') }}
  union all
  select
    *,
    'BASE' as artifact_source
  from {{ ref('stg_base__factories') }}
  union all
  select
    *,
    'FRAX' as artifact_source
  from {{ ref('stg_frax__factories') }}
  union all
  select
    *,
    'METAL' as artifact_source
  from {{ ref('stg_metal__factories') }}
  union all
  select
    *,
    'MODE' as artifact_source
  from {{ ref('stg_mode__factories') }}
  union all
  select
    *,
    'ZORA' as artifact_source
  from {{ ref('stg_zora__factories') }}
),

contract_deployments as (
  select
    artifact_source,
    transaction_hash,
    block_timestamp,
    deployer_address as root_deployer_address,
    deployer_address as created_by_address,
    contract_address,
    deployer_address as originating_eoa_address,
    'EOA' as creator_type,
    case
      when contract_address in (
        select distinct factory_address
        from factories
      ) then 'FACTORY'
      else 'CONTRACT'
    end as contract_type
  from deployers
),

factory_deployments as (
  select
    factories.artifact_source,
    factories.transaction_hash,
    factories.block_timestamp,
    deployers.deployer_address as root_deployer_address,
    factories.factory_address as created_by_address,
    factories.contract_address,
    'FACTORY' as creator_type,
    'CONTRACT' as contract_type,
    COALESCE(factories.originating_address, deployers.deployer_address)
      as originating_eoa_address
  from factories
  inner join deployers
    on factories.factory_address = deployers.contract_address
)

select
  artifact_source,
  root_deployer_address,
  contract_address,
  contract_type,
  created_by_address,
  creator_type,
  originating_eoa_address,
  transaction_hash,
  block_timestamp
from contract_deployments
union all
select
  artifact_source,
  root_deployer_address,
  contract_address,
  contract_type,
  created_by_address,
  creator_type,
  originating_eoa_address,
  transaction_hash,
  block_timestamp
from factory_deployments
