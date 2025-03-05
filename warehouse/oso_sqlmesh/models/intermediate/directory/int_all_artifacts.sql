MODEL (
  name oso.int_all_artifacts,
  description "a list of all artifacts associated with a project",
  kind FULL
);

/*
  Notes:
  - This will create a separate row for each artifact_type, which is de-duplicated
    in int_artifacts_by_project
  - Currently, the source and namespace for blockchain artifacts are the same.
    This may change in the future.
*/
WITH onchain_artifacts AS (
  SELECT
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    'DEPLOYER' AS artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_name AS artifact_url
  FROM oso.int_deployers_by_project
  UNION ALL
  SELECT
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    'CONTRACT' AS artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_name AS artifact_url
  FROM oso.int_contracts_by_project
), all_normalized_artifacts AS (
  SELECT
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM oso.int_artifacts_by_project_all_sources
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
  FROM onchain_artifacts
)
SELECT DISTINCT
  project_id,
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_normalized_artifacts