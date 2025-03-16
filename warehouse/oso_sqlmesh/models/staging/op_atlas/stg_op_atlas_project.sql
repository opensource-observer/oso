MODEL (
  name oso.stg_op_atlas_project,
  dialect trino,
  kind FULL
);

WITH latest_project AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS rn
  FROM @oso_source('bigquery.op_atlas.project')
  WHERE deleted_at IS NULL
)

SELECT
  @oso_id('OP_ATLAS', '', id)::VARCHAR AS project_id,
  id::VARCHAR AS project_source_id,
  'OP_ATLAS' AS project_source,
  '' AS project_namespace,
  id::VARCHAR AS project_name,
  name::VARCHAR AS display_name,
  description::VARCHAR,
  category::VARCHAR,
  thumbnail_url::VARCHAR,
  banner_url::VARCHAR,
  twitter::VARCHAR,
  mirror::VARCHAR,
  TRIM(LOWER(open_source_observer_slug))::VARCHAR AS open_source_observer_slug,
  created_at::TIMESTAMP,
  updated_at::TIMESTAMP,
  deleted_at::TIMESTAMP
FROM latest_project
WHERE rn = 1
