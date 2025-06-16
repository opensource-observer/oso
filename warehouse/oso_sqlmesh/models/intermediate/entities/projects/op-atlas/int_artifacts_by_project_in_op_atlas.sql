MODEL (
  name oso.int_artifacts_by_project_in_op_atlas,
  kind FULL,
  dialect trino,
  description "Unifies all artifacts from OP Atlas, including handling cases where contracts come in via OSO",
  audits (
    not_null(columns := (artifact_id, project_id))
  )
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
  WITH deployer_counts AS (
    SELECT
      artifact_source_id,
      COUNT(DISTINCT project_id) as project_count
    FROM oso.stg_op_atlas_project_deployer
    GROUP BY artifact_source_id
  )
  SELECT DISTINCT
    d.project_id,
    d.artifact_source_id,
    d.artifact_source,
    d.artifact_namespace,
    d.artifact_name,
    d.artifact_url,
    d.artifact_type
  FROM oso.stg_op_atlas_project_deployer d
  JOIN deployer_counts dc
    ON d.artifact_source_id = dc.artifact_source_id
  WHERE dc.project_count = 1
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
  UNION ALL
  SELECT
    op.project_id,
    dl.url AS artifact_source_id,
    'DEFILLAMA' AS artifact_source,
    '' AS artifact_namespace,
    dl.protocol AS artifact_name,
    dl.url AS artifact_url,
    'DEFILLAMA_PROTOCOL' AS artifact_type
  FROM oso.stg_op_atlas_project_defillama AS op
  JOIN oso.int_defillama_protocols AS dl
    ON op.artifact_name = dl.parent_protocol
    AND dl.parent_protocol IS NOT NULL
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
    AND LOWER(ossd.project_name) = LOWER(op_atlas.open_source_observer_slug)
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
  WHERE ossd_artifacts.artifact_type IN (
      'CONTRACT', 'DEPLOYER', 'DEFILLAMA_PROTOCOL', 'BRIDGE'
    )
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
