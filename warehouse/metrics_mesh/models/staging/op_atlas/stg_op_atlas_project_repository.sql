MODEL (
  name metrics.stg_op_atlas_project_repository,
  dialect trino,
  kind FULL,
);

select
  -- Translating op-atlas project_id to OSO project_id
  @oso_id('OP_ATLAS', project_id) as project_id,
  id as artifact_source_id,
  UPPER(type) as artifact_source,
  url as artifact_url,
  'REPOSITORY' as artifact_type,
  created_at,
  updated_at,
  verified as is_verified,
  open_source as is_open_source,
  contains_contracts,
  crate as contains_crates,
  npm_package as contains_npm
from @oso_source('bigquery.op_atlas.project_repository')