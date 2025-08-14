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

WITH parsed_artifacts AS (
  SELECT
    projects.account_slug,
    projects.account_name,
    projects.account_type,
    projects.account_id,
    gh_int.artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    parsed.artifact_type
  FROM oso.stg_open_collective__projects AS projects
  CROSS JOIN LATERAL @parse_github_repository_artifact(projects.social_link_url) AS parsed
  LEFT JOIN oso.int_artifacts__github AS gh_int
    ON gh_int.artifact_url = projects.social_link_url
  WHERE projects.social_link_url IS NOT NULL
    AND parsed.artifact_name IS NOT NULL
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
FROM parsed_artifacts