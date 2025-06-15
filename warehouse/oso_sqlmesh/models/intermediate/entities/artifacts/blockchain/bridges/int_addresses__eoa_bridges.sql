MODEL (
  name oso.int_addresses__eoa_bridges,
  kind FULL,
  dialect trino,
  partitioned_by "artifact_source",
  grain (project_id, artifact_source, artifact_id),
  description "Combines bridges with the ANY_EVM source",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_bridges AS (
  SELECT DISTINCT
    LOWER(bridges.address) AS artifact_name,
    LOWER(chains.chain) AS artifact_source,
  FROM oso.seed_known_eoa_bridges AS bridges
  CROSS JOIN oso.int_chain_id_to_chain_name AS chains
)

SELECT DISTINCT
  @oso_entity_id(artifact_source, '', artifact_name) AS artifact_id,
  artifact_source,
  artifact_name AS artifact_source_id,
  '' AS artifact_namespace,
  artifact_name
FROM all_bridges