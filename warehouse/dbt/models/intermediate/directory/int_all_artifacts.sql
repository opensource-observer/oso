{#
  This model is responsible for generating a list of all artifacts associated with a project.
  This includes repositories, npm packages, blockchain addresses, and contracts.

  Note: This will create a separate row for each artifact_type, which is de-duplicated
    in int_artifacts_by_project
  Note: Currently, the source and namespace for blockchain artifacts are the same. This may change
  in the future.
#}

with ossd_artifacts as (
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from {{ ref("int_artifacts_in_ossd_by_project") }}
),

verified_deployers as (
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    'DEPLOYER' as artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_name as artifact_url
  from {{ ref("int_deployers_by_project") }}
),

verified_contracts as (
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    'CONTRACT' as artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_name as artifact_url
  from {{ ref("int_contracts_by_project") }}
),

all_normalized_artifacts as (
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from ossd_artifacts
  union all
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from verified_deployers
  union all
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from verified_contracts
)

select distinct
  project_id,
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
from all_normalized_artifacts
