MODEL (
  name oso.int_bridges_by_project,
  kind FULL,
  dialect trino,
  partitioned_by "artifact_source",
  grain (project_id, artifact_source, artifact_id),
  description "Combines bridges with the ANY_EVM source",
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH base_bridges AS (
  SELECT DISTINCT
    project_id,
    artifact_source,
    artifact_name
  FROM oso.int_artifacts_by_project_all_sources
  WHERE
    artifact_type = 'BRIDGE'
), any_evm_matches AS (
  SELECT DISTINCT
    base.project_id,
    chains.chain AS artifact_source,
    base.artifact_name
  FROM base_bridges AS base
  CROSS JOIN oso.int_superchain_chain_names AS chains
  WHERE
    base.artifact_source = 'ANY_EVM'
), chain_specific_matches AS (
  SELECT DISTINCT
    base.project_id,
    base.artifact_source,
    base.artifact_name
  FROM base_bridges AS base
  WHERE
    base.artifact_source <> 'ANY_EVM'
), all_bridges AS (
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
FROM all_bridges