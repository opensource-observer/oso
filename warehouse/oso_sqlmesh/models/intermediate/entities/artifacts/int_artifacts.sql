MODEL (
  name oso.int_artifacts,
  description 'All artifacts',
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_artifacts AS (
  /*
    This grabs all the artifacts we know about from project sources
    and from the contract discovery process.
  */
  SELECT
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url,
    artifact_name
  FROM oso.int_artifacts_by_project
)
SELECT DISTINCT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url
FROM all_artifacts
