MODEL (
  name oso.stg_op_atlas_project,
  dialect trino,
  kind FULL
);

SELECT
  @oso_id('OP_ATLAS', id)::VARCHAR AS project_id,
  id::VARCHAR AS project_source_id,
  'OP_ATLAS' AS project_source,
  NULL::VARCHAR AS project_namespace,
  id::VARCHAR AS project_name,
  name::VARCHAR AS display_name,
  description::VARCHAR,
  category::VARCHAR,
  thumbnail_url::VARCHAR,
  banner_url::VARCHAR,
  twitter::VARCHAR,
  mirror::VARCHAR,
  open_source_observer_slug::VARCHAR,
  created_at::TIMESTAMP,
  updated_at::TIMESTAMP,
  deleted_at::TIMESTAMP
FROM @oso_source('bigquery.op_atlas.project')