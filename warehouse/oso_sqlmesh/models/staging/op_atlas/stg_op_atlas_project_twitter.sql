MODEL (
  name oso.stg_op_atlas_project_twitter,
  dialect trino,
  kind FULL
);

WITH sanitized AS (
  SELECT
    projects.project_id,
    'TWITTER' AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN projects.twitter LIKE 'https://twitter.com/%'
      THEN SUBSTRING(projects.twitter, 21)
      WHEN projects.twitter LIKE 'https://x.com/%'
      THEN SUBSTRING(projects.twitter, 15)
      WHEN projects.twitter LIKE '@%'
      THEN SUBSTRING(projects.twitter, 2)
      ELSE projects.twitter
    END AS artifact_name
  FROM oso.stg_op_atlas_project AS projects
)
SELECT
  project_id,
  CONCAT('https://x.com/', artifact_name) AS artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  'SOCIAL_HANDLE' AS artifact_type,
  CONCAT('https://x.com/', artifact_name) AS artifact_url
FROM sanitized