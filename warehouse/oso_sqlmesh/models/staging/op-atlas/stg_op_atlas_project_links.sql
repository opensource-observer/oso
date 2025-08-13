MODEL (
  name oso.stg_op_atlas_project_links,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT
    LOWER(project_id::TEXT) AS atlas_id,
    LOWER(url) AS url,
    updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project_links')
),

latest_data AS (
  SELECT
    atlas_id,
    url,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, url ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  url,
  updated_at
FROM latest_data
WHERE rn = 1