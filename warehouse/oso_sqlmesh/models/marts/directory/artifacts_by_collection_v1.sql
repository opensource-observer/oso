MODEL (
  name oso.artifacts_by_collection_v1,
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
  artifact_name,
  collection_id,
  collection_source,
  collection_namespace,
  collection_name
FROM oso.int_artifacts_by_collection