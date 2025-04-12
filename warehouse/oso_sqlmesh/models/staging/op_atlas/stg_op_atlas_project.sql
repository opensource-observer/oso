MODEL (
  name oso.stg_op_atlas_project,
  dialect trino,
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH cleaned_data AS (
  SELECT
    LOWER(id::VARCHAR) AS id,
    name,
    description,
    category,
    thumbnail_url,
    banner_url,
    twitter,
    mirror,
    TRIM(LOWER(open_source_observer_slug::VARCHAR)) AS open_source_observer_slug,
    created_at,
    updated_at,
    deleted_at
  FROM @oso_source('bigquery.op_atlas.project')
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
  WHERE deleted_at IS NULL
)

SELECT
  @oso_entity_id('OP_ATLAS', '', id) AS project_id,
  id AS project_source_id,
  'OP_ATLAS' AS project_source,
  '' AS project_namespace,
  id AS project_name,
  name AS display_name,
  description,
  category,
  thumbnail_url,
  banner_url,
  twitter,
  mirror,
  open_source_observer_slug,
  created_at,
  updated_at,
  deleted_at
FROM latest_data
WHERE rn = 1
