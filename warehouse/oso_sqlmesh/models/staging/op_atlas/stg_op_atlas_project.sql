MODEL (
  name oso.stg_op_atlas_project,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH project_slug_mappings AS (
  SELECT * FROM (
    VALUES 
      ('0x808b31862cec6dccf3894bb0e76ce4ca298e4c2820e2ccbf4816da740463b220', 'fractal-visions'),
      ('0xed3d54e5394dc3ed01f15a67fa6a70e203df31c928dad79f70e25cb84f6e2cf9', 'host-it'),
      ('0x15b210abdc6acfd99e60255792b2b78714f4e8c92c4c5e91b898d48d046212a4', 'defieye')
  ) AS t(atlas_id, oso_slug)
),

cleaned_data AS (
  SELECT
    LOWER(id::VARCHAR) AS id,
    name,
    description,
    category,
    thumbnail_url,
    banner_url,
    twitter,
    mirror,
    COALESCE(
      (SELECT oso_slug FROM project_slug_mappings WHERE LOWER(atlas_id) = LOWER(cleaned.id)),
      TRIM(LOWER(open_source_observer_slug::VARCHAR))
    ) AS open_source_observer_slug,
    created_at,
    updated_at,
    deleted_at
  FROM @oso_source('bigquery.op_atlas.project') AS cleaned
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
