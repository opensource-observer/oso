MODEL (
  name oso.int_artifacts_by_project_all_sources,
  kind FULL,
  dialect trino,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
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
    'CONTRACT' AS artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_name AS artifact_url
  FROM oso.int_artifacts_by_project_in_ossd_downstream
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
  unioned.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  unioned.artifact_id,
  unioned.artifact_source_id,
  unioned.artifact_source,
  unioned.artifact_type,
  unioned.artifact_namespace,
  unioned.artifact_name,
  unioned.artifact_url
FROM unioned
JOIN oso.int_projects AS projects
  ON unioned.project_id = projects.project_id