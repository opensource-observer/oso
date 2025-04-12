MODEL (
  name oso.projects_v1,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  projects.display_name,
  projects.description
FROM oso.int_projects AS projects