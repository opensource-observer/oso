MODEL (
  name oso.int_superchain_s7_devtooling_metrics_by_project,
  description "S7 metrics by devtooling project",
  dialect trino,
  kind full,
);

@DEF(min_package_connection_count, 3);
@DEF(min_developer_connection_count, 10);

WITH devtooling_projects AS (
  SELECT
    project_id,
    MIN(created_at) AS created_at,
    MAX(updated_at) AS updated_at,
    SUM(star_count) AS star_count,
    SUM(fork_count) AS fork_count,
    SUM(num_packages_in_deps_dev) AS num_packages_in_deps_dev
  FROM oso.int_superchain_s7_devtooling_repositories
  GROUP BY project_id
),

package_connections AS (
  SELECT
    deps_graph.devtooling_project_id AS project_id,
    COUNT(DISTINCT deps_graph.onchain_builder_project_id)
      AS package_connection_count,
    ARRAY_AGG(DISTINCT CAST(deps_graph.onchain_builder_project_id AS VARCHAR))
      AS package_connection_ids
  FROM oso.int_superchain_s7_devtooling_deps_to_projects_graph AS deps_graph
  GROUP BY deps_graph.devtooling_project_id
),

developer_connections AS (
  SELECT
    project_id,
    COUNT(DISTINCT developer_id) AS developer_connection_count,
    ARRAY_AGG(DISTINCT CAST(developer_name AS VARCHAR)) AS developer_names
  FROM oso.int_superchain_s7_devtooling_devs_to_projects_graph
  GROUP BY project_id
),

project_metrics AS (
  SELECT
    devtooling_projects.*,
    projects.project_name,
    projects.display_name,
    COALESCE(pkgs.package_connection_count, 0)
      AS package_connection_count,
    COALESCE(devs.developer_connection_count, 0)
      AS developer_connection_count,
    COALESCE(pkgs.package_connection_ids, CAST(ARRAY[] AS ARRAY(VARCHAR)))
      AS package_connection_ids,
    COALESCE(devs.developer_names, CAST(ARRAY[] AS ARRAY(VARCHAR)))
      AS developer_names
  FROM devtooling_projects
  JOIN oso.projects_v1 AS projects
    ON devtooling_projects.project_id = projects.project_id
  LEFT JOIN package_connections AS pkgs
    ON devtooling_projects.project_id = pkgs.project_id
  LEFT JOIN developer_connections AS devs
    ON devtooling_projects.project_id = devs.project_id
),

connected_project_names AS (
  SELECT 
    pm.project_id,
    ARRAY_AGG(DISTINCT CAST(builder_nodes.op_atlas_project_name AS VARCHAR))
      AS connected_project_names
  FROM project_metrics AS pm
  CROSS JOIN UNNEST(
    CASE 
      WHEN CARDINALITY(pm.package_connection_ids) > 0
      THEN pm.package_connection_ids 
      ELSE ARRAY[NULL] 
    END
  ) AS t(connection_id)
  JOIN oso.int_superchain_s7_devtooling_onchain_builder_nodes AS builder_nodes
    ON builder_nodes.project_id = t.connection_id
    AND t.connection_id IS NOT NULL
    AND builder_nodes.op_atlas_project_name IS NOT NULL
  GROUP BY pm.project_id
)

SELECT
  pm.project_id,
  pm.project_name,
  pm.display_name,
  pm.created_at,
  pm.updated_at,
  pm.star_count,
  pm.fork_count,
  pm.num_packages_in_deps_dev,
  pm.package_connection_count,
  COALESCE(cpn.connected_project_names, CAST(ARRAY[] AS ARRAY(VARCHAR)))
    AS connected_project_names,
  pm.developer_connection_count,
  pm.developer_names,
  CASE
    WHEN pm.package_connection_count >= @min_package_connection_count
      OR pm.developer_connection_count >= @min_developer_connection_count
    THEN TRUE
    ELSE FALSE
  END AS is_eligible
FROM project_metrics pm
LEFT JOIN connected_project_names cpn
  ON pm.project_id = cpn.project_id
