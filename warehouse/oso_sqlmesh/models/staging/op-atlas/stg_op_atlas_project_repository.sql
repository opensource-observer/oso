MODEL (
  name oso.stg_op_atlas_project_repository,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH manual_mappings AS (
  SELECT project_id, url FROM (VALUES
    ('0xc377ed1b705bcc856a628f961f1e7c8ca943e6f3727b7c179c657e227e8e852c', 'https://github.com/miguelmota/merkletreejs'),
    ('0x48220ef1d103189cd918e9290db4c4b99b463ae2817fb5ef0cc54556a7961b6f', 'https://github.com/miguelmota/keccak256'),
    ('0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8', 'https://github.com/ethereum/solc-js')
  ) AS x (project_id, url)
),

app_mappings_raw AS (
  SELECT
    LOWER(project_id::VARCHAR) AS project_id,
    LOWER(url) AS url,
    updated_at
  FROM @oso_source('bigquery.op_atlas.project_repository')
  WHERE
    verified = TRUE AND UPPER(type) = 'GITHUB'
),

app_mappings AS (
  SELECT *
  FROM (
    SELECT 
      *,
      ROW_NUMBER() OVER (PARTITION BY project_id, url ORDER BY updated_at DESC) AS rn
    FROM app_mappings_raw
  ) ranked
  WHERE rn = 1
),

combined_mappings AS (
  SELECT
    project_id,
    url
  FROM app_mappings AS a
  UNION ALL
  SELECT
    project_id,
    url
  FROM manual_mappings
),

op_atlas_repos AS (
  SELECT
    project_id,
    url,
    @url_parts(url, 2) AS artifact_namespace,
    @url_parts(url, 3) AS artifact_name,
    CONCAT('https://github.com/', @url_parts(url,2), '/', @url_parts(url,3))
      AS artifact_url
  FROM combined_mappings
)

SELECT DISTINCT
  @oso_entity_id('OP_ATLAS', '', op_atlas_repos.project_id) AS project_id,
  CASE
    WHEN all_repos.artifact_source_id IS NOT NULL
    THEN all_repos.artifact_source_id
    ELSE op_atlas_repos.artifact_url
  END AS artifact_source_id,
  'GITHUB' AS artifact_source,
  op_atlas_repos.artifact_namespace,
  op_atlas_repos.artifact_name,
  op_atlas_repos.artifact_url,
  'REPOSITORY' AS artifact_type
FROM op_atlas_repos
LEFT OUTER JOIN oso.int_github_repositories AS all_repos
  ON LOWER(op_atlas_repos.artifact_namespace) = all_repos.artifact_namespace
  AND LOWER(op_atlas_repos.artifact_name) = all_repos.artifact_name