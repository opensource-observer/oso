MODEL (
  name oso.int_artifacts_by_project_all_sources,
  kind FULL,
  dialect trino,
  partitioned_by (
    artifact_source,
    artifact_type,
    project_source
  ),
  grain (project_id, artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH unioned AS (
  SELECT * FROM oso.int_artifacts_by_project_all_unioned_not_distinct
  UNION ALL
  SELECT * FROM oso.int_artifacts_by_project_discovered
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