MODEL (
  name oso.int_superchain_s7_devtooling_metrics_by_project,
  description 'S7 devtooling metrics by project with various aggregations and filters',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id, metric_name)
);

WITH trusted_developers AS (
  SELECT
    developer_id,
    sample_date
  FROM oso.int_superchain_s7_trusted_developers
), all_dependencies /* Package dependency counts */ AS (
  SELECT
    devtooling_project_id AS project_id,
    'package_dependent_count' AS metric_name,
    COUNT(DISTINCT onchain_builder_project_id) AS amount,
    sample_date
  FROM oso.int_superchain_s7_project_to_dependency_graph
  GROUP BY
    devtooling_project_id,
    sample_date
), npm_dependencies AS (
  SELECT
    devtooling_project_id AS project_id,
    'npm_package_dependent_count' AS metric_name,
    COUNT(DISTINCT onchain_builder_project_id) AS amount,
    sample_date
  FROM oso.int_superchain_s7_project_to_dependency_graph
  WHERE
    dependency_source = 'NPM'
  GROUP BY
    devtooling_project_id,
    sample_date
), rust_dependencies AS (
  SELECT
    devtooling_project_id AS project_id,
    'cargo_package_dependent_count' AS metric_name,
    COUNT(DISTINCT onchain_builder_project_id) AS amount,
    sample_date
  FROM oso.int_superchain_s7_project_to_dependency_graph
  WHERE
    dependency_source = 'CARGO'
  GROUP BY
    devtooling_project_id,
    sample_date
), dev_connections /* Developer connections */ AS (
  SELECT
    devtooling_project_id AS project_id,
    'dev_connection_count' AS metric_name,
    COUNT(DISTINCT developer_id) AS amount,
    sample_date
  FROM oso.int_superchain_s7_project_to_developer_graph
  GROUP BY
    devtooling_project_id,
    sample_date
), trusted_dev_connections AS (
  SELECT
    dev_graph.devtooling_project_id AS project_id,
    'trusted_dev_connection_count' AS metric_name,
    COUNT(DISTINCT dev_graph.developer_id) AS amount,
    dev_graph.sample_date
  FROM oso.int_superchain_s7_project_to_developer_graph AS dev_graph
  INNER JOIN trusted_developers
    ON dev_graph.developer_id = trusted_developers.developer_id
    AND dev_graph.sample_date = trusted_developers.sample_date
  GROUP BY
    dev_graph.devtooling_project_id,
    dev_graph.sample_date
), repo_metrics /* Repository metrics */ AS (
  SELECT
    repos.project_id,
    oso.metric_name,
    oso.amount,
    dev_graph.sample_date
  FROM oso.int_repositories_enriched AS repos
  CROSS JOIN (
    SELECT
      'stars' AS metric_name,
      star_count AS amount
    FROM oso.int_repositories_enriched
    UNION ALL
    SELECT
      'forks' AS metric_name,
      fork_count AS amount
    FROM oso.int_repositories_enriched
  ) AS metrics
  /* Join to get sample dates from developer graph */
  INNER JOIN oso.int_superchain_s7_project_to_developer_graph AS dev_graph
    ON repos.project_id = dev_graph.devtooling_project_id
  GROUP BY
    repos.project_id,
    oso.metric_name,
    oso.amount,
    dev_graph.sample_date
), trusted_repo_metrics AS (
  SELECT
    dev_graph.devtooling_project_id AS project_id,
    CASE
      WHEN dev_graph.has_starred
      THEN 'trusted_stars'
      WHEN dev_graph.has_forked
      THEN 'trusted_forks'
    END AS metric_name,
    COUNT(DISTINCT dev_graph.developer_id) AS amount,
    dev_graph.sample_date
  FROM oso.int_superchain_s7_project_to_developer_graph AS dev_graph
  INNER JOIN trusted_developers
    ON dev_graph.developer_id = trusted_developers.developer_id
    AND dev_graph.sample_date = trusted_developers.sample_date
  WHERE
    dev_graph.has_starred OR dev_graph.has_forked
  GROUP BY
    dev_graph.devtooling_project_id,
    CASE
      WHEN dev_graph.has_starred
      THEN 'trusted_stars'
      WHEN dev_graph.has_forked
      THEN 'trusted_forks'
    END,
    dev_graph.sample_date
), package_metrics /* Package counts */ AS (
  SELECT
    devtooling_project_id AS project_id,
    'num_packages' AS metric_name,
    COUNT(DISTINCT dependency_name) AS amount,
    sample_date
  FROM oso.int_superchain_s7_project_to_dependency_graph
  GROUP BY
    devtooling_project_id,
    sample_date
)
/* Union all metrics together */
SELECT
  sample_date,
  project_id,
  metric_name,
  amount
FROM (
  SELECT
    *
  FROM all_dependencies
  UNION ALL
  SELECT
    *
  FROM npm_dependencies
  UNION ALL
  SELECT
    *
  FROM rust_dependencies
  UNION ALL
  SELECT
    *
  FROM dev_connections
  UNION ALL
  SELECT
    *
  FROM trusted_dev_connections
  UNION ALL
  SELECT
    *
  FROM repo_metrics
  UNION ALL
  SELECT
    *
  FROM trusted_repo_metrics
  UNION ALL
  SELECT
    *
  FROM package_metrics
)