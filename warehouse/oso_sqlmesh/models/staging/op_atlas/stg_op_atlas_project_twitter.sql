MODEL (
  name oso.stg_op_atlas_project_twitter,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH cleaned_data AS (
  SELECT
    LOWER(id::VARCHAR) AS project_id,
    LOWER(CASE
      WHEN twitter LIKE 'https://twitter.com/%'
      THEN SUBSTRING(twitter, 21)
      WHEN twitter LIKE 'https://x.com/%'
      THEN SUBSTRING(twitter, 15)
      WHEN twitter LIKE '@%'
      THEN SUBSTRING(twitter, 2)
      ELSE twitter
    END) AS twitter_handle,
    updated_at
  FROM @oso_source('bigquery.op_atlas.project') AS twitter
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, twitter_handle ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  CONCAT('https://x.com/', twitter_handle) AS artifact_source_id,
  'TWITTER' AS artifact_source,
  '' AS artifact_namespace,
  twitter_handle AS artifact_name,
  CONCAT('https://x.com/', twitter_handle) AS artifact_url,
  'SOCIAL_HANDLE' AS artifact_type
FROM latest_data
WHERE rn = 1