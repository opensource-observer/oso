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
  SELECT 
    abp_unioned.project_id,
    abp_unioned.artifact_id,
    abp_unioned.artifact_source_id,
    abp_unioned.artifact_source,
    abp_unioned.artifact_type,
    abp_unioned.artifact_namespace,
    abp_unioned.artifact_name,
    abp_unioned.artifact_url 
  FROM oso.int_artifacts_by_project_all_unioned_not_distinct as abp_unioned
  UNION ALL
  SELECT 
    discovered.project_id,
    discovered.artifact_id,
    discovered.artifact_source_id,
    discovered.artifact_source,
    discovered.artifact_type,
    discovered.artifact_namespace,
    discovered.artifact_name,
    discovered.artifact_url 
  FROM oso.int_artifacts_by_project_discovered as discovered
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