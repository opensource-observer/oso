MODEL (
  name metrics.stg_op_atlas_project,
  dialect trino,
  kind FULL,
);

select
  @oso_id('OP_ATLAS', id)::TEXT as project_id,
  id::TEXT as project_source_id,
  'OP_ATLAS' as project_source,
  null::TEXT as project_namespace,
  id::TEXT as project_name,
  name::TEXT as display_name,
  description::TEXT,
  category::TEXT,
  thumbnail_url::TEXT,
  banner_url::TEXT,
  twitter::TEXT,
  mirror::TEXT,
  open_source_observer_slug::TEXT,
  created_at::TIMESTAMP,
  updated_at::TIMESTAMP,
  deleted_at::TIMESTAMP,
from @oso_source('bigquery.op_atlas.project')