MODEL (
  name metrics.int_artifacts_by_project_in_op_atlas,
  kind FULL,
  dialect trino
);

with all_websites as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  from metrics.stg_op_atlas_project_website as sites
),

all_farcaster as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  from metrics.stg_op_atlas_project_farcaster as farcaster
),

all_twitter as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  from metrics.stg_op_atlas_project_twitter as twitter 
),

all_repository as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  from metrics.stg_op_atlas_project_repository
),

all_contracts as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  from metrics.stg_op_atlas_project_contract
),

all_defillama as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  from metrics.stg_op_atlas_project_defillama
),

all_artifacts as (
  select * from all_websites
  union all
  select * from all_farcaster
  union all
  select * from all_twitter
  union all
  select * from all_repository
  union all
  select * from all_contracts
  union all
  select * from all_defillama
),

all_normalized_artifacts as (
  select distinct
    project_id,
    LOWER(artifact_source_id) as artifact_source_id,
    UPPER(artifact_source) as artifact_source,
    LOWER(artifact_namespace) as artifact_namespace,
    LOWER(artifact_name) as artifact_name,
    LOWER(artifact_url) as artifact_url,
    UPPER(artifact_type) as artifact_type
  from all_artifacts
)

select
  project_id,
  @oso_id(artifact_source, artifact_source_id) as artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
from all_normalized_artifacts
