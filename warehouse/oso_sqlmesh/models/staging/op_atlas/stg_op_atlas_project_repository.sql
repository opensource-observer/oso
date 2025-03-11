MODEL (
  name oso.stg_op_atlas_project_repository,
  dialect trino,
  kind FULL
);

WITH latest_repositories AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, url ORDER BY updated_at DESC) AS rn
  FROM @oso_source('bigquery.op_atlas.project_repository')
  WHERE
    verified = TRUE AND UPPER(type) = 'GITHUB'
),

filtered_op_atlas_repos AS (
  SELECT
    @oso_id('OP_ATLAS', repos.project_id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
    'GITHUB' AS artifact_source,
    @url_parts(repos.url, 2) AS artifact_namespace,
    @url_parts(repos.url, 3) AS artifact_name,
    'REPOSITORY' AS artifact_type
  /* repos.created_at, */ /* repos.updated_at, */ /* repos.verified as is_verified, */ /* repos.open_source as is_open_source, */ /* repos.contains_contracts, */ /* repos.crate as contains_crates, */ /* repos.npm_package as contains_npm */
  FROM latest_repositories AS repos
  WHERE
    rn = 1
),

op_atlas_repos AS (
  SELECT
    *,
    CONCAT(
      'https://github.com/', artifact_namespace, '/', artifact_name
    ) AS artifact_url,
  FROM filtered_op_atlas_repos
)

SELECT
  op_atlas_repos.project_id,
  /* TODO: Remove this once we index the universe  */
  CASE
    WHEN ossd_repos.id IS NOT NULL THEN ossd_repos.id::VARCHAR
    ELSE op_atlas_repos.artifact_url
  END AS artifact_source_id,
  op_atlas_repos.artifact_source,
  op_atlas_repos.artifact_namespace,
  op_atlas_repos.artifact_name,
  op_atlas_repos.artifact_url,
  op_atlas_repos.artifact_type
FROM op_atlas_repos
LEFT OUTER JOIN oso.stg_ossd__current_repositories AS ossd_repos
  ON LOWER(op_atlas_repos.artifact_namespace) = LOWER(ossd_repos.owner)
  AND LOWER(op_atlas_repos.artifact_name) = LOWER(ossd_repos.name)
