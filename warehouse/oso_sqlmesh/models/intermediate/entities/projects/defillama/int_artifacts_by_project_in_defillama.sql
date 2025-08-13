MODEL (
  name oso.int_artifacts_by_project_in_defillama,
  kind FULL,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH metadata AS (
  SELECT
    category,
    'https://defillama.com/protocol/' || slug AS url,
    CASE
      WHEN parent_protocol IS NULL OR parent_protocol = '' THEN slug 
      ELSE REPLACE(parent_protocol, 'parent#', '') 
    END AS project_name,
    category AS project_display_name
  FROM oso.stg_defillama__protocol_metadata
),

urls_by_category AS (
  SELECT
    'DEFILLAMA' AS project_source,
    'protocol_metadata' AS project_namespace,
    metadata.project_name,
    metadata.project_name AS project_display_name,
    parsed.artifact_url AS artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    metadata.category
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
  @oso_entity_id(project_source, project_namespace, project_name)
    AS project_id,
  project_source,
  project_namespace,
  project_name,
  project_display_name,
  category
FROM urls_by_category