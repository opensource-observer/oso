MODEL (
  name oso.artifacts_by_project_v1,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM oso.int_artifacts_by_project