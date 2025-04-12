MODEL (
  name oso.artifacts_v1,
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
  artifact_name
FROM oso.int_artifacts