MODEL (
  name oso.int_collection_segments_analysis,
  description "Analysis view showing collection performance segments with comparative metrics",
  kind FULL,
  dialect trino,
  grain (segment),
  tags (
    'entity_category=collection',
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Aggregate statistics by segment for easy analysis
WITH segment_stats AS (
  SELECT
    segment,
    COUNT(*) AS collection_count,
    -- Developer metrics
    AVG(total_active_developers) AS avg_total_developers,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_active_developers) AS median_total_developers,
    MIN(total_active_developers) AS min_total_developers,
    MAX(total_active_developers) AS max_total_developers,
    -- Star metrics
    AVG(total_stars) AS avg_total_stars,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_stars) AS median_total_stars,
    -- Commit metrics
    AVG(total_commits) AS avg_total_commits,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_commits) AS median_total_commits,
    -- Project metrics
    AVG(total_projects) AS avg_projects_per_collection,
    SUM(total_projects) AS total_projects_in_segment,
    -- Quality metrics
    AVG(developer_density) AS avg_developer_density,
    AVG(commits_per_developer) AS avg_commits_per_developer,
    AVG(star_appeal) AS avg_star_appeal,
    AVG(active_dev_concentration) AS avg_top_20_concentration,
    -- Clustering quality
    AVG(silhouette) AS avg_silhouette_score
  FROM oso.int_collection_performance_clusters
  GROUP BY segment
),
overall_stats AS (
  SELECT
    SUM(total_active_developers) AS total_developers_all,
    SUM(total_stars) AS total_stars_all,
    SUM(total_projects) AS total_projects_all,
    COUNT(*) AS total_collections
  FROM oso.int_collection_performance_clusters
)

SELECT
  s.segment,
  s.collection_count,
  -- Segment share
  ROUND(100.0 * s.collection_count / NULLIF(o.total_collections, 0), 2) AS pct_of_collections,
  ROUND(100.0 * s.total_projects_in_segment / NULLIF(o.total_projects_all, 0), 2) AS pct_of_total_projects,
  -- Developer metrics
  CAST(s.avg_total_developers AS INTEGER) AS avg_total_developers,
  CAST(s.median_total_developers AS INTEGER) AS median_total_developers,
  CAST(s.min_total_developers AS INTEGER) AS min_total_developers,
  CAST(s.max_total_developers AS INTEGER) AS max_total_developers,
  -- Star metrics
  CAST(s.avg_total_stars AS INTEGER) AS avg_total_stars,
  CAST(s.median_total_stars AS INTEGER) AS median_total_stars,
  -- Commit metrics
  CAST(s.avg_total_commits AS INTEGER) AS avg_total_commits,
  CAST(s.median_total_commits AS INTEGER) AS median_total_commits,
  -- Project metrics
  ROUND(s.avg_projects_per_collection, 1) AS avg_projects_per_collection,
  CAST(s.total_projects_in_segment AS INTEGER) AS total_projects_in_segment,
  -- Quality metrics
  ROUND(s.avg_developer_density, 2) AS avg_developer_density,
  ROUND(s.avg_commits_per_developer, 1) AS avg_commits_per_developer,
  ROUND(s.avg_star_appeal, 1) AS avg_star_appeal,
  ROUND(s.avg_top_20_concentration, 3) AS avg_top_20_concentration,
  -- Clustering quality
  ROUND(s.avg_silhouette_score, 3) AS avg_silhouette_score,
  -- Custom segment sort order
  CASE s.segment
    WHEN 'Very Low' THEN 1
    WHEN 'Low' THEN 2
    WHEN 'Mid' THEN 3
    WHEN 'High' THEN 4
    WHEN 'Top' THEN 5
    ELSE 99
  END AS segment_sort_order
FROM segment_stats AS s
CROSS JOIN overall_stats AS o
ORDER BY segment_sort_order

