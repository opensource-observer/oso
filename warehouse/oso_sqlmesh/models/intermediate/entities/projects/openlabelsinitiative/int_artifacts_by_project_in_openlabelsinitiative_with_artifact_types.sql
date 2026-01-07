MODEL (
  name oso.int_artifacts_by_project_in_openlabelsinitiative_with_artifact_types,
  kind FULL,
  dialect trino,
  grain (project_id, artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  oli.project_id,
  oli.artifact_id,
  oli.artifact_source_id,
  oli.artifact_source,
  artifacts.artifact_type,
  oli.artifact_namespace,
  oli.artifact_name,
  oli.artifact_url
FROM oso.int_artifacts_by_project_in_openlabelsinitiative AS oli
INNER JOIN oso.int_artifacts__blockchain AS artifacts
  ON artifacts.artifact_id = oli.artifact_id
  AND artifacts.artifact_source = oli.artifact_source