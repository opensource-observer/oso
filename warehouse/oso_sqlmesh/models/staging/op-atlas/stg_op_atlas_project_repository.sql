MODEL (
  name oso.stg_op_atlas_project_repository,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT
    LOWER(pr.project_id::TEXT) AS atlas_id,
    LOWER(pr.url) AS repository_url,
    pr.updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project_repository') AS pr
  WHERE
    pr.verified = TRUE
    AND UPPER(pr.type) = 'GITHUB'
    AND pr.url IS NOT NULL
),

latest_data AS (
  SELECT
    atlas_id,
    repository_url,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, repository_url ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  repository_url,
  updated_at
FROM latest_data
WHERE rn = 1