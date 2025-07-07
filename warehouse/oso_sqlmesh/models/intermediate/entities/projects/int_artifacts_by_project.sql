MODEL (
  name oso.int_artifacts_by_project,
  kind FULL,
  dialect trino,
  partitioned_by (
    artifact_source,
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

SELECT DISTINCT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM oso.int_artifacts_by_project_all_sources