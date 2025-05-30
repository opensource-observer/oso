MODEL (
  name oso.int_projects__gitcoin,
  kind FULL,
  dialect trino,
  description "Unifies all projects from Gitcoin",
  audits (
    not_null(columns := (project_id))
  )
);

WITH projects AS (
  SELECT DISTINCT
    group_id,
    project_application_title
  FROM oso.stg_gitcoin__project_groups_summary
  WHERE total_amount_donated_in_usd > 0
)

SELECT DISTINCT
  @oso_entity_id('GITCOIN', '', group_id) AS project_id,
  'GITCOIN' AS project_source,
  '' AS project_namespace,
  group_id AS project_name,
  project_application_title AS display_name,
  '' AS description
FROM projects
