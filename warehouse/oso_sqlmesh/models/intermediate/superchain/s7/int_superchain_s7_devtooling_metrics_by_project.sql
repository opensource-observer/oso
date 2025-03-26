MODEL (
  name oso.int_superchain_s7_devtooling_metrics_by_project,
  description "S7 metrics by devtooling project (ready for JSON export)",
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
    COUNT(DISTINCT deps_graph.onchain_builder_project_id) AS package_connection_count,
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
    dp.project_id,
    proj.project_name,
    proj.display_name,
    dp.created_at,
    dp.updated_at,
    dp.star_count,
    dp.fork_count,
    dp.num_packages_in_deps_dev,
    COALESCE(pkgs.package_connection_count, 0) AS package_connection_count,
    COALESCE(devs.developer_connection_count, 0) AS developer_connection_count,
    COALESCE(devs.developer_names, CAST(ARRAY[] AS ARRAY(VARCHAR))) AS developer_names,
    CASE
      WHEN COALESCE(pkgs.package_connection_count, 0) >= @min_package_connection_count
        OR COALESCE(devs.developer_connection_count, 0) >= @min_developer_connection_count
      THEN TRUE
      ELSE FALSE
    END AS is_eligible
  FROM devtooling_projects dp
  JOIN oso.projects_v1 proj
    ON dp.project_id = proj.project_id
  LEFT JOIN package_connections pkgs
    ON dp.project_id = pkgs.project_id
  LEFT JOIN developer_connections devs
    ON dp.project_id = devs.project_id
)

SELECT
  m.project_name,
  m.display_name,
  m.is_eligible,
  m.project_id AS oso_project_id,
  m.star_count AS project_star_count,
  m.fork_count AS project_fork_count,
  m.package_connection_count,
  m.developer_connection_count,
  filter(
    ARRAY_AGG(DISTINCT CASE 
                         WHEN g.onchain_builder_project_id IS NOT NULL 
                         THEN g.onchain_builder_project_id 
                       END),
    x -> x IS NOT NULL
  ) AS onchain_builder_oso_project_ids,
  filter(
    ARRAY_AGG(DISTINCT CASE 
                         WHEN g.onchain_builder_op_atlas_project_id IS NOT NULL 
                         THEN g.onchain_builder_op_atlas_project_id 
                       END),
    x -> x IS NOT NULL
  ) AS onchain_builder_op_atlas_ids,
  m.developer_names AS trusted_developer_usernames
FROM project_metrics m
LEFT JOIN oso.int_superchain_s7_devtooling_graph g
  ON m.project_id = g.devtooling_project_id
GROUP BY
  m.project_name,
  m.display_name,
  m.is_eligible,
  m.project_id,
  m.star_count,
  m.fork_count,
  m.package_connection_count,
  m.developer_connection_count,
  m.developer_names;