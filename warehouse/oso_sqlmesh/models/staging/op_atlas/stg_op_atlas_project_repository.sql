MODEL (
  name metrics.stg_op_atlas_project_repository,
  dialect trino,
  kind FULL,
);

select
  -- Translating op-atlas project_id to OSO project_id
  @oso_id('OP_ATLAS', repos.project_id) as project_id,
  repos.id as artifact_source_id,
  UPPER(repos.type) as artifact_source,
  @url_parts(repos.url, 2) as artifact_namespace,
  @url_parts(repos.url, 3) as artifact_name,
  repos.url as artifact_url,
  'REPOSITORY' as artifact_type,
  --repos.created_at,
  --repos.updated_at,
  --repos.verified as is_verified,
  --repos.open_source as is_open_source,
  --repos.contains_contracts,
  --repos.crate as contains_crates,
  --repos.npm_package as contains_npm
from @oso_source('bigquery.op_atlas.project_repository') as repos