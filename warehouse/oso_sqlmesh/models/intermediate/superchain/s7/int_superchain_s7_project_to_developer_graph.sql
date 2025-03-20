MODEL (
  name oso.int_superchain_s7_project_to_developer_graph,
  description 'Temp table - will delete after S7 migration',
  dialect trino,
  kind full,
);

SELECT *
FROM oso.int_superchain_s7_devtooling_devs_to_projects_graph
