MODEL (
  name oso.int_artifacts_by_project_all_sources,
  kind FULL,
  dialect trino
);

WITH unioned AS (
  SELECT
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM oso.int_artifacts_by_project_in_ossd
  UNION ALL
  SELECT
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM oso.int_artifacts_by_project_in_op_atlas
)
SELECT DISTINCT
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  unioned.*
FROM unioned
JOIN oso.int_projects AS projects
  ON unioned.project_id = projects.project_id