MODEL (
  name oso.int_artifacts_by_project_in_openlabelsinitiative,
  kind FULL,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH addresses_by_project AS (
  SELECT
    chain AS artifact_source,
    parsed.artifact_name AS artifact_source_id,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    'OPENLABELSINITIATIVE' AS project_source,
    'owner_project' AS project_namespace,
    COALESCE(owner_project, 'unknown') AS project_name,
    usage_category
  FROM oso.int_addresses__openlabelsinitiative
  CROSS JOIN LATERAL @parse_blockchain_artifact(address) AS parsed
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
  usage_category
FROM addresses_by_project