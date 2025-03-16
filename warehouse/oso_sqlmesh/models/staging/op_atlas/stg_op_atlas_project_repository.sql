MODEL (
  name oso.stg_op_atlas_project_repository,
  dialect trino,
  kind FULL
);

WITH cleaned_data AS (
  SELECT
    LOWER(project_id::VARCHAR) AS project_id,
    LOWER(url) AS url,
    updated_at
  FROM @oso_source('bigquery.op_atlas.project_repository')
  WHERE
    verified = TRUE AND UPPER(type) = 'GITHUB'
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, url ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
),

op_atlas_repos AS (
  SELECT
    project_id,
    url,
    @url_parts(url, 2) AS artifact_namespace,
    @url_parts(url, 3) AS artifact_name,
    CONCAT('https://github.com/', @url_parts(url,2), '/', @url_parts(url,3)) AS artifact_url
  FROM latest_data
  WHERE rn = 1
)

SELECT
  @oso_entity_id('OP_ATLAS', '', op_atlas_repos.project_id) AS project_id,
  /* TODO: Remove this once we index the universe  */
  CASE
    WHEN ossd_repos.id IS NOT NULL THEN ossd_repos.id::VARCHAR
    ELSE op_atlas_repos.artifact_url
  END AS artifact_source_id,
  'GITHUB' AS artifact_source,
  op_atlas_repos.artifact_namespace,
  op_atlas_repos.artifact_name,
  op_atlas_repos.artifact_url,
  'REPOSITORY' AS artifact_type
FROM op_atlas_repos
LEFT OUTER JOIN oso.stg_ossd__current_repositories AS ossd_repos
  ON LOWER(op_atlas_repos.artifact_namespace) = LOWER(ossd_repos.owner)
  AND LOWER(op_atlas_repos.artifact_name) = LOWER(ossd_repos.name)