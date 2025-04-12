MODEL (
  name oso.int_projects,
  description 'All projects',
  kind FULL,
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
    project_id,
    project_source,
    project_namespace,
    project_name,
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