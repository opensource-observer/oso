MODEL (
  name oso.int_ddp_repo_features,
  description "Developer Data Program repositories with features for clustering analysis",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  partitioned_by bucket(artifact_id, 16),
  tags (
    'entity_category=artifact',
    'index={"idx_artifact_id": ["artifact_id"]}',
    'order_by=["artifact_id"]'
  ),
  physical_properties (
    parquet_bloom_filter_columns = ['artifact_id'],
    sorted_by = ['artifact_id']
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Pre-aggregate maintainer counts to reduce join size
WITH maintainer_counts AS (
  SELECT
    artifact_namespace,
    COUNT(*) AS num_repos_owned_by_maintainer
  FROM oso.int_ddp_repo_metadata
  GROUP BY artifact_namespace
),

-- Get only the artifact_ids we need from base metadata first
base_artifact_ids AS (
  SELECT DISTINCT artifact_id
  FROM oso.int_ddp_repo_metadata
),

-- Pre-aggregate packages to reduce join size
packages_agg AS (
  SELECT
    package_owner_artifact_id AS artifact_id,
    COUNT(DISTINCT package_artifact_id) AS package_count,
    CAST(TRUE AS BOOLEAN) AS has_packages
  FROM oso.int_packages__current_maintainer_only
  WHERE package_owner_artifact_id IN (SELECT artifact_id FROM base_artifact_ids)
  GROUP BY package_owner_artifact_id
),

-- Pre-aggregate commit times to reduce join size
commit_times AS (
  SELECT
    artifact_id,
    MIN(first_commit_time) AS first_commit_time,
    MAX(last_commit_time) AS last_commit_time
  FROM oso.int_first_last_commit_to_github_repository
  WHERE artifact_id IN (SELECT artifact_id FROM base_artifact_ids)
  GROUP BY artifact_id
),

-- Select only needed columns from base metadata
base_metadata AS (
  SELECT
    bm.artifact_id,
    bm.artifact_namespace,
    bm.artifact_name,
    bm.artifact_url,
    bm.is_fork,
    bm.created_at,
    bm.updated_at,
    bm.star_count,
    bm.fork_count,
    bm.language,
    bm.is_ethereum,
    bm.is_evm_l1,
    bm.is_evm_l2,
    bm.is_evm_stack,
    bm.is_solana,
    bm.ecosystem_count,
    bm.is_in_ossd,
    bm.is_owner_in_ossd,
    mc.num_repos_owned_by_maintainer
  FROM oso.int_ddp_repo_metadata AS bm
  INNER JOIN maintainer_counts AS mc
    ON bm.artifact_namespace = mc.artifact_namespace
),

-- Pre-filter lineage to only DDP repos to reduce join size
lineage_filtered AS (
  SELECT
    artifact_id,
    is_current_url,
    alias_count
  FROM oso.int_ddp_repo_lineage
  WHERE artifact_id IN (SELECT artifact_id FROM base_artifact_ids)
),

-- Pre-filter metrics to only DDP repos to reduce join size
metrics_filtered AS (
  SELECT
    artifact_id,
    contributor_count,
    commit_count,
    fork_count,
    star_count,
    opened_issue_count,
    closed_issue_count,
    opened_pull_request_count,
    merged_pull_request_count,
    release_count,
    comment_count
  FROM oso.int_ddp_repo_metrics_pivoted
  WHERE artifact_id IN (SELECT artifact_id FROM base_artifact_ids)
),

-- Pre-filter github users to only relevant namespaces to reduce join size
github_users_filtered AS (
  SELECT DISTINCT artifact_name
  FROM oso.int_github_users
  WHERE artifact_name IN (SELECT DISTINCT artifact_namespace FROM oso.int_ddp_repo_metadata)
),

-- Join in optimal order: start with base, then join smaller aggregated tables
joined AS (
  SELECT
    bm.artifact_id,
    bm.artifact_url AS url,
    bm.artifact_namespace AS repo_maintainer,
    bm.artifact_name AS repo_name,
    COALESCE(gu.artifact_name IS NOT NULL, FALSE) AS is_personal_repo,
    bm.num_repos_owned_by_maintainer,
    COALESCE(lin.is_current_url, TRUE) AS is_current_repo,
    COALESCE(lin.alias_count, 0) AS alias_count,
    COALESCE(bm.language, 'Unknown') AS language,
    CASE
      WHEN bm.is_fork THEN 'Yes'
      WHEN bm.is_fork IS NULL THEN 'Unknown'
      ELSE 'No'
    END AS fork_status,
    COALESCE(bm.created_at, ct.first_commit_time) AS first_activity_time,
    COALESCE(bm.updated_at, ct.last_commit_time) AS last_activity_time,
    COALESCE(bm.fork_count, pm.fork_count) AS fork_count,
    COALESCE(bm.star_count, pm.star_count) AS star_count,
    COALESCE(pm.contributor_count, 0) AS contributor_count,
    COALESCE(pm.commit_count, 0) AS commit_count,
    COALESCE(pm.opened_issue_count, 0) AS opened_issue_count,
    COALESCE(pm.closed_issue_count, 0) AS closed_issue_count,
    COALESCE(pm.opened_pull_request_count, 0) AS opened_pull_request_count,
    COALESCE(pm.merged_pull_request_count, 0) AS merged_pull_request_count,
    COALESCE(pm.release_count, 0) AS release_count,
    COALESCE(pm.comment_count, 0) AS comment_count,
    COALESCE(rp.has_packages, FALSE) AS has_packages,
    COALESCE(rp.package_count, 0) AS package_count,
    bm.is_ethereum,
    bm.is_evm_l1,
    bm.is_evm_l2,
    bm.is_evm_stack,
    bm.is_solana,
    bm.ecosystem_count,
    bm.is_in_ossd,
    bm.is_owner_in_ossd
  FROM base_metadata AS bm
  LEFT JOIN lineage_filtered AS lin
    ON bm.artifact_id = lin.artifact_id
  LEFT JOIN commit_times AS ct
    ON bm.artifact_id = ct.artifact_id
  LEFT JOIN metrics_filtered AS pm
    ON bm.artifact_id = pm.artifact_id
  LEFT JOIN packages_agg AS rp
    ON bm.artifact_id = rp.artifact_id
  LEFT JOIN github_users_filtered AS gu
    ON bm.artifact_namespace = gu.artifact_name
)

SELECT
  artifact_id,
  url,
  repo_maintainer,
  repo_name,
  is_personal_repo,
  num_repos_owned_by_maintainer,
  is_current_repo,
  alias_count,
  language,
  fork_status,
  first_activity_time,
  last_activity_time,
  -- Calculate age in months from first to last activity
  CASE
    WHEN first_activity_time IS NOT NULL AND last_activity_time IS NOT NULL
    THEN DATE_DIFF('month', first_activity_time, last_activity_time)
    ELSE NULL
  END AS age_months,
  contributor_count,
  commit_count,
  fork_count,
  star_count,
  opened_issue_count,
  closed_issue_count,
  opened_pull_request_count,
  merged_pull_request_count,
  release_count,
  comment_count,
  has_packages,
  package_count,
  is_ethereum,
  is_evm_l1,
  is_evm_l2,
  is_evm_stack,
  is_solana,
  ecosystem_count,
  is_in_ossd,
  is_owner_in_ossd
FROM joined
