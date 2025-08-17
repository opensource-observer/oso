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
    artifacts.artifact_type,
    oli.artifact_namespace,
    oli.artifact_name,
    oli.artifact_url
  FROM oso.int_artifacts_by_project_in_openlabelsinitiative AS oli
  LEFT JOIN oso.int_artifacts AS artifacts
    ON artifacts.artifact_id = oli.artifact_id
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