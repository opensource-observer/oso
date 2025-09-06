MODEL (
  name oso.int_artifacts,
  description 'All artifacts',
  kind FULL,
  partitioned_by ("artifact_source", "artifact_type"),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_artifacts AS (
  SELECT
    artifact_source_id,
    'GITHUB' AS artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.int_artifacts__github
  UNION ALL
  SELECT
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.int_artifacts__blockchain
  UNION ALL
  SELECT
    url AS artifact_source_id,
    'DEFILLAMA' AS artifact_source,
    '' AS artifact_namespace,
    protocol AS artifact_name,
    url AS artifact_url,
    'DEFILLAMA_PROTOCOL' AS artifact_type
  FROM oso.int_defillama_protocols
  UNION ALL
  SELECT
    package_artifact_name AS artifact_source_id,
    package_artifact_source AS artifact_source,
    package_artifact_namespace AS artifact_namespace,
    package_artifact_name AS artifact_name,
    package_artifact_url AS artifact_url,
    'PACKAGE' AS artifact_type
  FROM oso.int_packages__current_maintainer_only
)

SELECT DISTINCT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_artifacts
