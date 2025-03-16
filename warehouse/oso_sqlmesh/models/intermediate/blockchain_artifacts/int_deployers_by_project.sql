MODEL (
  name oso.int_deployers_by_project,
  kind FULL,
  partitioned_by "artifact_namespace",
  description "Combines deployers from any EVM chain and chain-specific deployers"
);

WITH base_deployers AS (
  SELECT DISTINCT
    project_id,
    artifact_source,
    artifact_name
  FROM oso.int_artifacts_by_project_all_sources
  WHERE
    artifact_type = 'DEPLOYER'
), any_evm_matches AS (
  SELECT DISTINCT
    base.project_id,
    deployers.chain AS artifact_source,
    deployers.deployer_address AS artifact_name
  FROM oso.int_deployers AS deployers
  INNER JOIN base_deployers AS base
    ON deployers.deployer_address = base.artifact_name
  WHERE
    base.artifact_source = 'ANY_EVM'
), chain_specific_matches AS (
  SELECT DISTINCT
    base.project_id,
    deployers.chain AS artifact_source,
    deployers.deployer_address AS artifact_name
  FROM oso.int_deployers AS deployers
  INNER JOIN base_deployers AS base
    ON deployers.deployer_address = base.artifact_name
    AND deployers.chain = base.artifact_source
  WHERE
    base.artifact_source <> 'ANY_EVM'
), all_deployers AS (
  SELECT
    *
  FROM any_evm_matches
  UNION ALL
  SELECT
    *
  FROM chain_specific_matches
)
SELECT DISTINCT
  project_id,
  @oso_entity_id(artifact_source, '', artifact_name) AS artifact_id,
  artifact_source,
  artifact_name AS artifact_source_id,
  '' AS artifact_namespace,
  artifact_name
FROM all_deployers