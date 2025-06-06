MODEL (
  name oso.int_artifacts_by_project__open_collective,
  kind FULL,
  dialect trino,
  description "Unifies GitHub artifacts from Open Collective projects",
  audits (
    not_null(columns := (artifact_id, project_id))
  )
);

WITH specific_repos AS (
  SELECT DISTINCT
    account_slug,
    artifact_namespace,
    artifact_name,
    artifact_url AS artifact_source_id,
    artifact_url
  FROM oso.stg_open_collective__projects
  WHERE artifact_url IS NOT NULL
    AND artifact_name IS NOT NULL
),

org_repos AS (
  SELECT DISTINCT
    project_repos.account_slug,
    project_repos.artifact_namespace,
    all_repos.artifact_name,
    all_repos.artifact_source_id,
    all_repos.artifact_url
  FROM oso.stg_open_collective__projects AS project_repos
  CROSS JOIN oso.int_github_repositories AS all_repos
  WHERE project_repos.artifact_url IS NOT NULL
    AND project_repos.artifact_name IS NULL
    AND project_repos.artifact_namespace = all_repos.artifact_namespace
),

all_repos AS (
  SELECT * FROM specific_repos
  UNION ALL
  SELECT * FROM org_repos
)

SELECT DISTINCT
  @oso_entity_id('OPEN_COLLECTIVE', '', account_slug) AS project_id,
  @oso_entity_id('GITHUB', artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  'GITHUB' AS artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  'REPOSITORY' AS artifact_type
FROM all_repos