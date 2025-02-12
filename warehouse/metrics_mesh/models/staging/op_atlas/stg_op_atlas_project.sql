MODEL (
  name metrics.stg_op_atlas_project,
  dialect trino,
  kind FULL,
);

select
  @oso_id('OP_ATLAS', id) as project_id,
  'OP_ATLAS' as project_source,
  null as project_namespace,
  id as project_name,
  name as display_name,
  description,
  category,
  thumbnail_url,
  banner_url,
  twitter,
  mirror,
  open_source_observer_slug,
  created_at,
  updated_at,
  deleted_at,
from @oso_source('bigquery.op_atlas.project')