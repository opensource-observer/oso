MODEL (
  name oso.int_artifacts_by_project_in_open_collective,
  kind FULL,
  dialect trino,
  description "Unifies GitHub artifacts from Open Collective projects",
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    not_null(columns := (artifact_id, project_id))
  )
);

WITH github_urls AS (
  SELECT
    id AS account_id,
    slug AS account_slug,
    name AS account_name,
    type AS account_type,
    CASE 
      WHEN github_handle IS NOT NULL THEN CONCAT('https://github.com/', github_handle)
      WHEN repository_url IS NOT NULL THEN repository_url
      ELSE NULL
    END AS github_url
  FROM oso.stg_open_collective__accounts
  WHERE github_handle IS NOT NULL OR repository_url IS NOT NULL
),

parsed_github_artifacts AS (
  SELECT
    github_urls.account_slug,
    github_urls.account_name,
    github_urls.account_type,
    github_urls.account_id,
    gh_int.artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    parsed.artifact_type
  FROM github_urls
  CROSS JOIN LATERAL @parse_github_repository_artifact(github_urls.github_url) AS parsed
  LEFT JOIN oso.int_artifacts__github AS gh_int
    ON gh_int.artifact_url = github_urls.github_url
  WHERE github_urls.github_url IS NOT NULL
    AND parsed.artifact_name IS NOT NULL
),

wallet_artifacts AS (
  SELECT
    accounts.slug AS account_slug,
    accounts.name AS account_name,
    accounts.type AS account_type,
    accounts.id AS account_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM oso.stg_open_collective__accounts AS accounts
  CROSS JOIN LATERAL @create_open_collective_wallet_artifact(accounts.slug) AS artifact_fields
),

all_artifacts AS (
  SELECT * FROM parsed_github_artifacts
  UNION ALL
  SELECT * FROM wallet_artifacts
)

SELECT DISTINCT
  @oso_entity_id('OPEN_COLLECTIVE', '', account_slug) AS project_id,
  'OPEN_COLLECTIVE' AS project_source,
  '' AS project_namespace,
  account_slug AS project_name,
  account_name AS project_display_name,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  artifact_source_id
FROM all_artifacts