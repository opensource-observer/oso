MODEL (
  name oso.int_artifacts_by_collection_in_openlabelsinitiative,
  kind FULL,
  tags (
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH addresses_by_category AS (
  SELECT
    chain AS artifact_source,
    parsed.artifact_name AS artifact_source_id,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    'OPENLABELSINITIATIVE' AS collection_source,
    'usage_category' AS collection_namespace,
    LOWER(usage_category) AS collection_name,
    usage_category AS collection_display_name
  FROM oso.int_addresses__openlabelsinitiative
  CROSS JOIN LATERAL @parse_blockchain_artifact(address) AS parsed
  WHERE usage_category IS NOT NULL
)

SELECT DISTINCT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  @oso_entity_id(collection_source, collection_namespace, collection_name)
    AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name
FROM addresses_by_category