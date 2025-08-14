MODEL (
  name oso.int_superchain_s7_trusted_developers,
  description 'Maps relationships between trusted developers and devtooling projects',
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  enabled false,
);

SELECT DISTINCT
  project_id,
  developer_id,
  developer_name
FROM oso.int_superchain_s7_devtooling_devs_to_projects_graph
