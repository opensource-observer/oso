MODEL (
  name oso.stg_op_atlas_project,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT
    LOWER(id::TEXT) AS atlas_id,
    name::TEXT AS name,
    description::TEXT AS description,
    category::TEXT AS category,
    LOWER(thumbnail_url::TEXT) AS thumbnail_url,
    LOWER(banner_url::TEXT) AS banner_url,
    LOWER(twitter::TEXT) AS twitter_url,
    LOWER(open_source_observer_slug::TEXT) AS open_source_observer_slug,
    created_at::TIMESTAMP AS created_at,
    updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project')
  WHERE deleted_at IS NULL
),

latest_data AS (
  SELECT
    atlas_id,
    name,
    description,
    category,
    thumbnail_url,
    banner_url,
    twitter_url,
    open_source_observer_slug,
    created_at,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  name AS display_name,
  description,
  category,
  thumbnail_url,
  banner_url,
  twitter_url,
  open_source_observer_slug,
  created_at,
  updated_at
FROM latest_data
WHERE rn = 1