MODEL (
  name oso.int_artifacts_by_project,
  kind FULL
);

SELECT DISTINCT
  artifacts.artifact_id,
  artifacts.artifact_source_id,
  artifacts.artifact_source,
  artifacts.artifact_namespace,
  artifacts.artifact_name,
  artifacts.artifact_url,
  artifacts.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
FROM oso.int_all_artifacts AS artifacts
LEFT JOIN oso.int_projects AS projects
  ON artifacts.project_id = projects.project_id
WHERE
  NOT artifacts.project_id IS NULL