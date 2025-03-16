MODEL (
  name oso.int_artifacts_by_project_in_op_atlas,
  kind FULL,
  dialect trino,
  description "Unifies all artifacts from OP Atlas, including handling cases where contracts come in via OSO"
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
  FROM oso.stg_op_atlas_project_website
),
all_farcaster AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_farcaster
),
all_twitter AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_twitter
),
all_repository AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_repository
),
all_contracts AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_contract
),
all_deployers AS (
  SELECT DISTINCT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_deployer
),
all_defillama AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM oso.stg_op_atlas_project_defillama
),
all_artifacts AS (
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
), 
-- Handle case where contracts come in via OSO
oso_linked_projects AS (
  SELECT
    op_atlas.project_id AS op_atlas_project_id,
    ossd.project_id AS ossd_project_id,
    op_atlas.open_source_observer_slug
  FROM oso.stg_op_atlas_project AS op_atlas
  JOIN oso.int_projects AS ossd
    ON ossd.project_source = 'OSS_DIRECTORY'
    AND ossd.project_name = op_atlas.open_source_observer_slug
  WHERE op_atlas.open_source_observer_slug IS NOT NULL
),
-- Get artifacts from OSSD for the linked projects
oso_artifacts AS (
  SELECT
    linked.op_atlas_project_id AS project_id,
    ossd_artifacts.artifact_source_id,
    ossd_artifacts.artifact_source,
    ossd_artifacts.artifact_namespace,
    ossd_artifacts.artifact_name,
    ossd_artifacts.artifact_url,
    ossd_artifacts.artifact_type
  FROM oso_linked_projects AS linked
  JOIN oso.int_artifacts_by_project_in_ossd AS ossd_artifacts
    ON linked.ossd_project_id = ossd_artifacts.project_id
  WHERE ossd_artifacts.artifact_type IN ('CONTRACT', 'DEPLOYER')
    AND NOT EXISTS (
      SELECT 1
      FROM all_artifacts  AS op_atlas_artifacts
      WHERE 
        op_atlas_artifacts.project_id = linked.op_atlas_project_id
        AND op_atlas_artifacts.artifact_source = ossd_artifacts.artifact_source
        AND op_atlas_artifacts.artifact_name = ossd_artifacts.artifact_name
    )
),
all_combined_artifacts AS (
  SELECT * FROM all_artifacts
  UNION ALL
  SELECT * FROM oso_artifacts
),
all_normalized_artifacts AS (
  SELECT DISTINCT
    project_id,
    LOWER(artifact_source_id) AS artifact_source_id,
    UPPER(artifact_source) AS artifact_source,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    LOWER(artifact_url) AS artifact_url,
    UPPER(artifact_type) AS artifact_type
  FROM all_combined_artifacts
  WHERE artifact_name IS NOT NULL
)
SELECT
  project_id,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_normalized_artifacts
