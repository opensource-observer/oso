MODEL(
  name oso.int_labeled_addresses_all_sources,
  description 'Normalized table of labeled addresses from all sources',
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH oli_labeled_addresses AS (
  SELECT DISTINCT
    address,
    chain,
    owner_project,
    'OLI' AS labeling_source
  FROM oso.int_addresses__openlabelsinitiative
),
atlas_labeled_addresses AS (
  SELECT DISTINCT
    artifact_name AS address,
    artifact_source AS chain,
    atlas_id AS owner_project,
    'OP_ATLAS' AS labeling_source
  FROM oso.int_artifacts_by_project_in_op_atlas
  WHERE artifact_type IN ('DEPLOYER', 'CONTRACT')
),
ossd_labeled_addresses AS (
  SELECT DISTINCT
    artifacts.artifact_name AS address,
    artifacts.artifact_source AS chain,
    ossd_projects.project_name AS owner_project,
    'OSS_DIRECTORY' AS labeling_source
  FROM oso.int_artifacts_by_project_in_ossd AS artifacts
  JOIN oso.projects_v1 AS ossd_projects
    ON artifacts.project_id = ossd_projects.project_id
  WHERE artifacts.artifact_type IN ('DEPLOYER', 'CONTRACT', 'EOA', 'BRIDGE')
),
all_labeled_addresses AS (  
  SELECT * FROM oli_labeled_addresses
  UNION ALL
  SELECT * FROM atlas_labeled_addresses
  UNION ALL
  SELECT * FROM ossd_labeled_addresses
)

SELECT
  @oso_entity_id(chain, '', address) AS artifact_id,
  address,
  chain,
  owner_project,
  labeling_source
FROM all_labeled_addresses



