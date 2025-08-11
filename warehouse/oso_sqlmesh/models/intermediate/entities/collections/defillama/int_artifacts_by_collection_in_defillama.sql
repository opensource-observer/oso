MODEL (
  name oso.int_artifacts_by_collection_in_defillama,
  kind FULL,
  tags (
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH metadata AS (
  SELECT
    'https://defillama.com/protocol/' || slug AS url,
    category
  FROM oso.stg_defillama__protocol_metadata
),

urls_by_category AS (
  SELECT
    'DEFILLAMA' AS collection_source,
    'category' AS collection_namespace,
    REPLACE(LOWER(metadata.category), ' ', '_') AS collection_name,
    metadata.category AS collection_display_name,
    parsed.artifact_url AS artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url
  FROM metadata
  CROSS JOIN LATERAL @parse_defillama_artifact(metadata.url) AS parsed
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
FROM urls_by_category