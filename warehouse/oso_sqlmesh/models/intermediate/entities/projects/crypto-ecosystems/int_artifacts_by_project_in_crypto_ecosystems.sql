MODEL (
  name oso.int_artifacts_by_project_in_crypto_ecosystems,
  description "Many-to-many mapping of GitHub repositories to Crypto Ecosystems with both 'eco' and 'branch' project namespaces",
  kind FULL,
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    not_null(columns := (artifact_id, project_id))
  )
);

WITH parsed_artifacts AS (
  SELECT
    taxonomy.eco_name,
    taxonomy.branch,
    gh_int.artifact_source_id,
    parsed_url.artifact_namespace,
    parsed_url.artifact_name,
    parsed_url.artifact_url,
    parsed_url.artifact_type
  FROM oso.stg_crypto_ecosystems__taxonomy AS taxonomy
  CROSS JOIN LATERAL @parse_github_repository_artifact(taxonomy.repo_url) AS parsed_url
  LEFT JOIN oso.int_artifacts__github AS gh_int
    ON gh_int.artifact_url = taxonomy.repo_url
  WHERE taxonomy.repo_url LIKE 'https://github.com%'
),

eco_projects AS (
  SELECT
    'CRYPTO_ECOSYSTEMS' AS project_source,
    'eco' AS project_namespace,
    @to_entity_name(eco_name) AS project_name,
    eco_name AS project_display_name,
    'GITHUB' AS artifact_source,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM parsed_artifacts
  WHERE eco_name IS NOT NULL
),

branch_projects AS (
  SELECT
    'CRYPTO_ECOSYSTEMS' AS project_source,
    'branch' AS project_namespace,
    @to_entity_name(b.branch_name) AS project_name,
    b.branch_name AS project_display_name,
    'GITHUB' AS artifact_source,
    parsed_artifacts.artifact_source_id,
    parsed_artifacts.artifact_namespace,
    parsed_artifacts.artifact_name,
    parsed_artifacts.artifact_url,
    parsed_artifacts.artifact_type
  FROM parsed_artifacts
  CROSS JOIN UNNEST(parsed_artifacts.branch) AS b(branch_name)
  WHERE b.branch_name IS NOT NULL
),

all_project_mappings AS (
  SELECT * FROM eco_projects
  UNION ALL
  SELECT * FROM branch_projects
)

SELECT DISTINCT
  @oso_entity_id(project_source, project_namespace, project_name)
    AS project_id,
  project_source,
  project_namespace,
  project_name,
  project_display_name,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS artifact_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  artifact_source_id
FROM all_project_mappings