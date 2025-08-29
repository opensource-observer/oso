MODEL (
  name oso.int_projects,
  description 'All projects',
  kind FULL,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ossd_projects AS (
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    COALESCE(display_name, project_name) AS display_name,
    description
  FROM oso.stg_ossd__current_projects
), op_atlas_projects AS (
  SELECT
    @oso_entity_id('OP_ATLAS', '', atlas_id) AS project_id,
    'OP_ATLAS' AS project_source,
    '' AS project_namespace,
    atlas_id AS project_name,
    display_name,
    description
  FROM oso.stg_op_atlas_project
), crypto_ecosystem_projects AS (
  SELECT DISTINCT
    project_id,
    project_source,
    project_namespace,
    project_name,
    project_display_name AS display_name,
    NULL::VARCHAR AS description
  FROM oso.int_artifacts_by_project_in_crypto_ecosystems
), defillama_projects AS (
  SELECT DISTINCT
    project_id,
    project_source,
    project_namespace,
    project_name,
    project_display_name AS display_name,
    NULL::VARCHAR AS description
  FROM oso.int_artifacts_by_project_in_defillama
), openlabels_projects AS (
  SELECT DISTINCT
    oli.project_id,
    oli.project_source,
    oli.project_namespace,
    oli.project_name,
    COALESCE(ossd_projects.display_name, oli.project_name) AS display_name,
    NULL::VARCHAR AS description
  FROM oso.int_artifacts_by_project_in_openlabelsinitiative AS oli
  LEFT JOIN ossd_projects
    ON oli.project_name = ossd_projects.project_name
)
SELECT
  *
FROM ossd_projects
UNION ALL
SELECT
  *
FROM op_atlas_projects
UNION ALL
SELECT
  *
FROM crypto_ecosystem_projects
UNION ALL
SELECT
  *
FROM defillama_projects
UNION ALL
SELECT
  *
FROM openlabels_projects