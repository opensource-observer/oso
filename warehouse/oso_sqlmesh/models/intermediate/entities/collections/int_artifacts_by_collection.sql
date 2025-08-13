MODEL (
  name oso.int_artifacts_by_collection,
  kind FULL,
  tags (
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  artifacts.artifact_id,
  artifacts.artifact_source_id,
  artifacts.artifact_source,
  artifacts.artifact_namespace,
  artifacts.artifact_name,
  artifacts.artifact_url,
  projects_by_collection.collection_id,
  projects_by_collection.collection_source,
  projects_by_collection.collection_namespace,
  projects_by_collection.collection_name
FROM oso.int_artifacts_by_project AS artifacts
LEFT JOIN oso.int_projects_by_collection AS projects_by_collection
  ON artifacts.project_id = projects_by_collection.project_id
WHERE
  NOT projects_by_collection.collection_id IS NULL
