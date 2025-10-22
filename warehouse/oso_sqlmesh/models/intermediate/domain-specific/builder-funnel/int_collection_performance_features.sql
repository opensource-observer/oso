MODEL (
  name oso.int_collection_performance_features,
  description "Performance features for each collection to be used in clustering",
  kind FULL,
  dialect trino,
  grain (collection_id, sample_date),
  tags (
    'entity_category=collection',
    'model_category=clustering'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    unique_values(columns := (collection_id, sample_date)),
    not_null(columns := (collection_id, sample_date))
  )
);

-- Aggregate performance metrics at the collection level for the most recent date
WITH latest_dates AS (
  SELECT 
    collection_id,
    MAX(sample_date) AS max_date
  FROM oso.int_ranked_projects_by_collection
  GROUP BY collection_id
),
ranked_projects AS (
  SELECT
    rpc.collection_id,
    rpc.collection_source,
    rpc.collection_namespace,
    rpc.collection_name,
    rpc.collection_display_name,
    rpc.sample_date,
    rpc.metric_id,
    rpc.metric_model,
    COUNT(DISTINCT rpc.project_id) AS project_count,
    SUM(rpc.amount) AS total_amount,
    AVG(rpc.amount) AS avg_amount,
    MAX(rpc.amount) AS max_amount,
    MIN(rpc.amount) AS min_amount,
    STDDEV(rpc.amount) AS stddev_amount,
    -- Top project concentration: what % of total is from top 20% of projects
    SUM(CASE WHEN rpc.percentile_rank >= 0.8 THEN rpc.amount ELSE 0 END) / NULLIF(SUM(rpc.amount), 0) AS top_20_concentration
  FROM oso.int_ranked_projects_by_collection AS rpc
  INNER JOIN latest_dates AS ld
    ON rpc.collection_id = ld.collection_id
    AND rpc.sample_date = ld.max_date
  GROUP BY
    rpc.collection_id,
    rpc.collection_source,
    rpc.collection_namespace,
    rpc.collection_name,
    rpc.collection_display_name,
    rpc.sample_date,
    rpc.metric_id,
    rpc.metric_model
),
-- Pivot key metrics into columns for easier feature engineering
pivoted_metrics AS (
  SELECT
    collection_id,
    collection_source,
    collection_namespace,
    collection_name,
    collection_display_name,
    sample_date,
    -- Active developers metrics
    MAX(CASE WHEN metric_model = 'active_developers' THEN total_amount END) AS total_active_developers,
    MAX(CASE WHEN metric_model = 'active_developers' THEN avg_amount END) AS avg_active_developers_per_project,
    MAX(CASE WHEN metric_model = 'active_developers' THEN top_20_concentration END) AS active_dev_concentration,
    -- Stars metrics
    MAX(CASE WHEN metric_model = 'stars' THEN total_amount END) AS total_stars,
    MAX(CASE WHEN metric_model = 'stars' THEN avg_amount END) AS avg_stars_per_project,
    -- Commits metrics
    MAX(CASE WHEN metric_model = 'commits' THEN total_amount END) AS total_commits,
    MAX(CASE WHEN metric_model = 'commits' THEN avg_amount END) AS avg_commits_per_project,
    -- Forks metrics
    MAX(CASE WHEN metric_model = 'forks' THEN total_amount END) AS total_forks,
    -- Contributors metrics
    MAX(CASE WHEN metric_model = 'contributors' THEN total_amount END) AS total_contributors,
    MAX(CASE WHEN metric_model = 'contributors' THEN avg_amount END) AS avg_contributors_per_project,
    -- Project diversity
    MAX(project_count) AS total_projects
  FROM ranked_projects
  GROUP BY
    collection_id,
    collection_source,
    collection_namespace,
    collection_name,
    collection_display_name,
    sample_date
)

SELECT
  collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name,
  sample_date,
  -- Core metrics (coalesce to 0 if null)
  COALESCE(total_active_developers, 0) AS total_active_developers,
  COALESCE(avg_active_developers_per_project, 0) AS avg_active_developers_per_project,
  COALESCE(active_dev_concentration, 0) AS active_dev_concentration,
  COALESCE(total_stars, 0) AS total_stars,
  COALESCE(avg_stars_per_project, 0) AS avg_stars_per_project,
  COALESCE(total_commits, 0) AS total_commits,
  COALESCE(avg_commits_per_project, 0) AS avg_commits_per_project,
  COALESCE(total_forks, 0) AS total_forks,
  COALESCE(total_contributors, 0) AS total_contributors,
  COALESCE(avg_contributors_per_project, 0) AS avg_contributors_per_project,
  COALESCE(total_projects, 0) AS total_projects,
  -- Derived features
  COALESCE(total_active_developers, 0) / NULLIF(total_projects, 0) AS developer_density,
  COALESCE(total_commits, 0) / NULLIF(total_active_developers, 0) AS commits_per_developer,
  COALESCE(total_stars, 0) / NULLIF(total_projects, 0) AS star_appeal
FROM pivoted_metrics

