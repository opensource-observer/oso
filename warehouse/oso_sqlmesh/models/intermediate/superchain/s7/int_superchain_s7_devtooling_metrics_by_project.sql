MODEL (
  name oso.int_superchain_s7_devtooling_metrics_by_project,
  description "S7 metrics by devtooling project",
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
    ARRAY_AGG(DISTINCT projects.project_name) AS package_connection_names
  FROM oso.int_superchain_s7_devtooling_deps_to_projects_graph AS deps_graph
  JOIN oso.projects_v1 AS projects
    ON deps_graph.onchain_builder_project_id = projects.project_id
  GROUP BY deps_graph.devtooling_project_id
),

developer_connections AS (
  SELECT
    project_id,
    COUNT(DISTINCT developer_id) AS developer_connection_count,
    ARRAY_AGG(DISTINCT developer_name) AS developer_names
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
    COALESCE(pkgs.package_connection_names, ARRAY[]::TEXT[])
      AS package_connection_names,
    COALESCE(devs.developer_names, ARRAY[]::TEXT[])
      AS developer_names
  FROM devtooling_projects
  JOIN oso.projects_v1 AS projects
    ON devtooling_projects.project_id = projects.project_id
  LEFT JOIN package_connections AS pkgs
    ON devtooling_projects.project_id = pkgs.project_id
  LEFT JOIN developer_connections AS devs
    ON devtooling_projects.project_id = devs.project_id
)

SELECT
  project_id,
  project_name,
  display_name,
  created_at,
  updated_at,
  star_count,
  fork_count,
  num_packages_in_deps_dev,
  package_connection_count,
  package_connection_names,
  developer_connection_count,
  developer_names,
  CASE
    WHEN package_connection_count >= @min_package_connection_count
      OR developer_connection_count >= @min_developer_connection_count
    THEN TRUE
    ELSE FALSE
  END AS is_eligible
FROM project_metrics