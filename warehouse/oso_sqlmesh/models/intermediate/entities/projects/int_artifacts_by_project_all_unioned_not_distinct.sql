MODEL (
  name oso.int_artifacts_by_project_all_unioned_not_distinct,
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
  artifact_type,
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
FROM oso.int_artifacts_by_project_in_op_atlas_downstream
UNION ALL
SELECT
  project_id,
  artifact_id,
  artifact_source_id,
  artifact_source,
  'REPOSITORY' AS artifact_type,
  artifact_namespace,
  artifact_name,
  artifact_url
FROM oso.int_artifacts_by_project_in_crypto_ecosystems
UNION ALL
SELECT
  project_id,
  artifact_id,
  artifact_source_id,
  artifact_source,
  'DEFILLAMA_PROTOCOL' AS artifact_type,
  artifact_namespace,
  artifact_name,
  artifact_url
FROM oso.int_artifacts_by_project_in_defillama
UNION ALL
SELECT
  oli.project_id,
  oli.artifact_id,
  oli.artifact_source_id,
  oli.artifact_source,
  oli.artifact_type,
  oli.artifact_namespace,
  oli.artifact_name,
  oli.artifact_url
FROM oso.int_artifacts_by_project_in_openlabelsinitiative_with_artifact_types AS oli