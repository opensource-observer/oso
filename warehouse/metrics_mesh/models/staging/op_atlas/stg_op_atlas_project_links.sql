MODEL (
  name metrics.stg_op_atlas_project_links,
  dialect trino,
  kind FULL,
);

select
  -- Translating op-atlas project_id to OSO project_id
  @oso_id('OP_ATLAS', project_id) as project_id,
  url as artifact_url,
  id as artifact_source_id,
  name as display_name,
  description,
  created_at,
  updated_at,
from @oso_source('bigquery.op_atlas.project_links')