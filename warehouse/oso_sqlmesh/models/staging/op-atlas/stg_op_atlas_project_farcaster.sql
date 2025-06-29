MODEL (
  name oso.stg_op_atlas_project_farcaster,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT
    LOWER(p.id::TEXT) AS atlas_id,
    LOWER(fc.value) AS farcaster_url,
    p.updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project__farcaster') AS fc
  INNER JOIN @oso_source('bigquery.op_atlas.project') AS p
    ON fc._dlt_parent_id = p._dlt_id
),

latest_data AS (
  SELECT
    atlas_id,
    farcaster_url,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, farcaster_url ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  farcaster_url,
  updated_at
FROM latest_data
WHERE rn = 1
