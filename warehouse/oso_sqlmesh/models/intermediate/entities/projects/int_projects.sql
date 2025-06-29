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
    display_name,
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
)
SELECT
  *
FROM ossd_projects
UNION ALL
SELECT
  *
FROM op_atlas_projects
