MODEL (
  name oso.artifacts_v1,
  kind FULL,
  tags (
    'export'
  )
);

SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name
FROM oso.int_artifacts