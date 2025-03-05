MODEL (
  name oso.int_artifacts_by_project_in_op_atlas,
  kind FULL,
  dialect trino
);

WITH all_websites AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_website AS sites
), all_farcaster AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_farcaster AS farcaster
), all_twitter AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_twitter AS twitter
), all_repository AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_repository
), all_contracts AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_contract
), all_deployers AS (
  SELECT DISTINCT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_deployer
), all_defillama AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_defillama
), all_artifacts AS (
  SELECT
    *
  FROM all_websites
  UNION ALL
  SELECT
    *
  FROM all_farcaster
  UNION ALL
  SELECT
    *
  FROM all_twitter
  UNION ALL
  SELECT
    *
  FROM all_repository
  UNION ALL
  SELECT
    *
  FROM all_contracts
  UNION ALL
  SELECT
    *
  FROM all_deployers
  UNION ALL
  SELECT
    *
  FROM all_defillama
), all_normalized_artifacts AS (
  SELECT DISTINCT
    project_id,
    LOWER(artifact_source_id) AS artifact_source_id,
    UPPER(artifact_source) AS artifact_source,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    LOWER(artifact_url) AS artifact_url,
    UPPER(artifact_type) AS artifact_type
  FROM all_artifacts
)
SELECT
  project_id,
  @oso_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_normalized_artifacts