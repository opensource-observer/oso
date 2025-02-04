MODEL (
  name metrics.int_deployers_by_project,
  description 'All deployers by project',
  kind FULL,
  partitioned_by "artifact_namespace",
);

with all_deployers as (
  select * from metrics.int_deployers
),

known_deployers as (
  select distinct
    project_id,
    artifact_source,
    artifact_name
  from metrics.int_artifacts_in_ossd_by_project
  where artifact_type = 'DEPLOYER'
),

any_evm_deployers as (
  select
    known_deployers.project_id,
    all_deployers.deployer_address,
    all_deployers.chain
  from all_deployers
  left join known_deployers
    on all_deployers.deployer_address = known_deployers.artifact_name
  where
    known_deployers.project_id is not null
    and known_deployers.artifact_source = 'ANY_EVM'
),

chain_specific_deployers as (
  select
    known_deployers.project_id,
    all_deployers.deployer_address,
    all_deployers.chain
  from all_deployers
  left join known_deployers
    on
      all_deployers.deployer_address = known_deployers.artifact_name
      and all_deployers.chain = known_deployers.artifact_source
  where
    known_deployers.project_id is not null
    and known_deployers.artifact_source != 'ANY_EVM'
),

verified_deployers as (
  select
    project_id,
    deployer_address,
    chain
  from any_evm_deployers
  union all
  select
    project_id,
    deployer_address,
    chain 
  from chain_specific_deployers
),

deployers as (
  select distinct
    project_id,
    deployer_address as artifact_name,
    chain as artifact_source
  from verified_deployers
)

select
  project_id,
  @oso_id(artifact_source, artifact_name) as artifact_id,
  artifact_source,
  artifact_name as artifact_source_id,
  LOWER(artifact_source) as artifact_namespace,
  artifact_name
from deployers
