MODEL (
  name oso.stg_op_atlas_project_farcaster,
  dialect trino,
  kind FULL
);

WITH cleaned_data AS (
  SELECT
    LOWER(projects.id::VARCHAR) AS project_id,
    LOWER(CASE
      WHEN farcaster.value LIKE 'https://warpcast.com/%'
      THEN SUBSTRING(farcaster.value, 22)
      WHEN farcaster.value LIKE '/%'
      THEN SUBSTRING(farcaster.value, 2)
      WHEN farcaster.value LIKE '@%'
      THEN SUBSTRING(farcaster.value, 2)
      ELSE farcaster.value
    END) AS farcaster_handle,
    projects.updated_at AS updated_at
  FROM @oso_source('bigquery.op_atlas.project__farcaster') AS farcaster
  INNER JOIN @oso_source('bigquery.op_atlas.project') AS projects
    ON farcaster._dlt_parent_id = projects._dlt_id
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, farcaster_handle ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  /* TODO: This should be FID */
  CONCAT('https://warpcast.com/', farcaster_handle) AS artifact_source_id,
  'FARCASTER' AS artifact_source,
  '' AS artifact_namespace,
  farcaster_handle AS artifact_name,
  CONCAT('https://warpcast.com/', farcaster_handle) AS artifact_url,
  'SOCIAL_HANDLE' AS artifact_type
FROM latest_data
WHERE rn = 1