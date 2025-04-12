MODEL (
  name oso.int_artifacts_by_project,
  kind FULL,
  dialect trino,
  grain (project_id, artifact_id),
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT DISTINCT
  artifacts.artifact_id,
  artifacts.artifact_source_id,
  artifacts.artifact_source,
  artifacts.artifact_namespace,
  artifacts.artifact_name,
  artifacts.artifact_url,
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
FROM oso.int_all_artifacts AS artifacts
JOIN oso.int_projects AS projects
  ON artifacts.project_id = projects.project_id