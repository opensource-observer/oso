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
)
SELECT
  @oso_id('OP_ATLAS', repos.project_id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
  repos.id AS artifact_source_id,
  'GITHUB' AS artifact_source,
  @url_parts(repos.url, 2) AS artifact_namespace,
  @url_parts(repos.url, 3) AS artifact_name,
  repos.url AS artifact_url,
  'REPOSITORY' AS artifact_type
/* repos.created_at, */ /* repos.updated_at, */ /* repos.verified as is_verified, */ /* repos.open_source as is_open_source, */ /* repos.contains_contracts, */ /* repos.crate as contains_crates, */ /* repos.npm_package as contains_npm */
FROM latest_repositories AS repos
WHERE
  rn = 1