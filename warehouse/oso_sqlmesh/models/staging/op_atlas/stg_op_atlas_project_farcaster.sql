MODEL (
  name oso.stg_op_atlas_project_farcaster,
  dialect trino,
  kind FULL
);

WITH sanitized AS (
  SELECT
    @oso_id('OP_ATLAS', '', projects.id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
    'FARCASTER' AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN farcaster.value LIKE 'https://warpcast.com/%'
      THEN SUBSTRING(farcaster.value, 22)
      WHEN farcaster.value LIKE '/%'
      THEN SUBSTRING(farcaster.value, 2)
      WHEN farcaster.value LIKE '@%'
      THEN SUBSTRING(farcaster.value, 2)
      ELSE farcaster.value
    END AS artifact_name /* Right now they don't validate */ /* so the value can either be a handle or URL */
  FROM @oso_source('bigquery.op_atlas.project__farcaster') AS farcaster
  INNER JOIN @oso_source('bigquery.op_atlas.project') AS projects
    ON farcaster._dlt_parent_id = projects._dlt_id
)
SELECT
  project_id,
  CONCAT('https://warpcast.com/', artifact_name)
    AS artifact_source_id, /* TODO: Shouldn't this be FID? */
  artifact_source,
  artifact_namespace,
  artifact_name,
  'SOCIAL_HANDLE' AS artifact_type,
  CONCAT('https://warpcast.com/', artifact_name) AS artifact_url
FROM sanitized
