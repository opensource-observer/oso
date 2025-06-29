MODEL (
  name oso.stg_op_atlas_project_website,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data AS (
  SELECT
    LOWER(p.id::TEXT) AS atlas_id,
    LOWER(pw.value) AS website_url,
    p.updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project__website') AS pw
  INNER JOIN @oso_source('bigquery.op_atlas.project') AS p
    ON pw._dlt_parent_id = p._dlt_id
),

latest_data AS (
  SELECT
    atlas_id,
    website_url,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, website_url ORDER BY updated_at DESC) AS rn
  FROM source_data
)

SELECT
  atlas_id,
  website_url,
  updated_at
FROM latest_data
WHERE rn = 1