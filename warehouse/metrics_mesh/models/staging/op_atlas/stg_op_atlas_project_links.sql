MODEL (
  name metrics.stg_op_atlas_project_links,
  dialect trino,
  kind FULL,
);

select
  -- Translating op-atlas project_id to OSO project_id
  @oso_id('OP_ATLAS', project_id) as project_id,
  id as artifact_source_id,
  'WWW' as artifact_source,
  'WWW' as artifact_namespace,
  url as artifact_name,
  url as artifact_url,
  'WEBSITE' as artifact_type,
  name as display_name,
  description,
  created_at,
  updated_at
from @oso_source('bigquery.op_atlas.project_links')