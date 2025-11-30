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

-- Get only the artifact_ids we need from base metadata first (materialized)
WITH base_artifact_ids AS (
  SELECT artifact_id
  FROM oso.int_ddp_repo_metadata
),

-- Pre-aggregate maintainer counts to reduce join size
maintainer_counts AS (
  SELECT
    artifact_namespace,
    COUNT(*) AS num_repos_owned_by_maintainer
  FROM oso.int_ddp_repo_metadata
  GROUP BY artifact_namespace
),

-- Pre-aggregate packages to reduce join size (using EXISTS for better performance)
packages_agg AS (
  SELECT
    pkg.package_owner_artifact_id AS artifact_id,
    COUNT(DISTINCT pkg.package_artifact_id) AS package_count,
    CAST(TRUE AS BOOLEAN) AS has_packages
  FROM oso.int_packages__current_maintainer_only AS pkg
  WHERE EXISTS (SELECT 1 FROM base_artifact_ids AS b WHERE b.artifact_id = pkg.package_owner_artifact_id)
  GROUP BY pkg.package_owner_artifact_id
),

-- Pre-aggregate commit times to reduce join size (using EXISTS for better performance)
commit_times AS (
  SELECT
    ct.artifact_id,
    MIN(ct.first_commit_time) AS first_commit_time,
    MAX(ct.last_commit_time) AS last_commit_time
  FROM oso.int_first_last_commit_to_github_repository AS ct
  WHERE EXISTS (SELECT 1 FROM base_artifact_ids AS b WHERE b.artifact_id = ct.artifact_id)
  GROUP BY ct.artifact_id
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

-- Pre-filter lineage to only DDP repos to reduce join size (using EXISTS)
lineage_filtered AS (
  SELECT
    lin.artifact_id,
    lin.is_current_url,
    lin.alias_count
  FROM oso.int_ddp_repo_lineage AS lin
  WHERE EXISTS (SELECT 1 FROM base_artifact_ids AS b WHERE b.artifact_id = lin.artifact_id)
),

-- Pre-filter metrics to only DDP repos to reduce join size (using EXISTS)
metrics_filtered AS (
  SELECT
    pm.artifact_id,
    pm.contributor_count,
    pm.commit_count,
    pm.fork_count,
    pm.star_count,
    pm.opened_issue_count,
    pm.closed_issue_count,
    pm.opened_pull_request_count,
    pm.merged_pull_request_count,
    pm.release_count,
    pm.comment_count
  FROM oso.int_ddp_repo_metrics_pivoted AS pm
  WHERE EXISTS (SELECT 1 FROM base_artifact_ids AS b WHERE b.artifact_id = pm.artifact_id)
),

-- Pre-filter github users to only relevant namespaces to reduce join size
namespace_list AS (
  SELECT DISTINCT artifact_namespace
  FROM oso.int_ddp_repo_metadata
  WHERE artifact_namespace IS NOT NULL
),

github_users_filtered AS (
  SELECT DISTINCT gu.artifact_name
  FROM oso.int_github_users AS gu
  WHERE EXISTS (SELECT 1 FROM namespace_list AS n WHERE n.artifact_namespace = gu.artifact_name)
),

-- Join in stages: first join smaller tables, then larger ones
-- Stage 1: Join base with metrics (most selective, likely to have most matches)
base_with_metrics AS (
  SELECT
    bm.artifact_id,
    bm.artifact_url,
    bm.artifact_namespace,
    bm.artifact_name,
    bm.is_fork,
    bm.created_at,
    bm.updated_at,
    bm.language,
    bm.num_repos_owned_by_maintainer,
    bm.is_ethereum,
    bm.is_evm_l1,
    bm.is_evm_l2,
    bm.is_evm_stack,
    bm.is_solana,
    bm.ecosystem_count,
    bm.is_in_ossd,
    bm.is_owner_in_ossd,
    COALESCE(bm.fork_count, pm.fork_count) AS fork_count,
    COALESCE(bm.star_count, pm.star_count) AS star_count,
    COALESCE(pm.contributor_count, 0) AS contributor_count,
    COALESCE(pm.commit_count, 0) AS commit_count,
    COALESCE(pm.opened_issue_count, 0) AS opened_issue_count,
    COALESCE(pm.closed_issue_count, 0) AS closed_issue_count,
    COALESCE(pm.opened_pull_request_count, 0) AS opened_pull_request_count,
    COALESCE(pm.merged_pull_request_count, 0) AS merged_pull_request_count,
    COALESCE(pm.release_count, 0) AS release_count,
    COALESCE(pm.comment_count, 0) AS comment_count
  FROM base_metadata AS bm
  LEFT JOIN metrics_filtered AS pm
    ON bm.artifact_id = pm.artifact_id
),

-- Stage 2: Add commit times and lineage
base_with_metrics_and_times AS (
  SELECT
    bwm.*,
    COALESCE(bwm.created_at, ct.first_commit_time) AS first_activity_time,
    COALESCE(bwm.updated_at, ct.last_commit_time) AS last_activity_time,
    COALESCE(lin.is_current_url, TRUE) AS is_current_repo,
    COALESCE(lin.alias_count, 0) AS alias_count
  FROM base_with_metrics AS bwm
  LEFT JOIN commit_times AS ct
    ON bwm.artifact_id = ct.artifact_id
  LEFT JOIN lineage_filtered AS lin
    ON bwm.artifact_id = lin.artifact_id
),

-- Stage 3: Add packages and github users (smallest tables last)
joined AS (
  SELECT
    bwt.artifact_id,
    bwt.artifact_url AS url,
    bwt.artifact_namespace AS repo_maintainer,
    bwt.artifact_name AS repo_name,
    COALESCE(gu.artifact_name IS NOT NULL, FALSE) AS is_personal_repo,
    bwt.num_repos_owned_by_maintainer,
    bwt.is_current_repo,
    bwt.alias_count,
    COALESCE(bwt.language, 'Unknown') AS language,
    CASE
      WHEN bwt.is_fork THEN 'Yes'
      WHEN bwt.is_fork IS NULL THEN 'Unknown'
      ELSE 'No'
    END AS fork_status,
    bwt.first_activity_time,
    bwt.last_activity_time,
    bwt.fork_count,
    bwt.star_count,
    bwt.contributor_count,
    bwt.commit_count,
    bwt.opened_issue_count,
    bwt.closed_issue_count,
    bwt.opened_pull_request_count,
    bwt.merged_pull_request_count,
    bwt.release_count,
    bwt.comment_count,
    COALESCE(rp.has_packages, FALSE) AS has_packages,
    COALESCE(rp.package_count, 0) AS package_count,
    bwt.is_ethereum,
    bwt.is_evm_l1,
    bwt.is_evm_l2,
    bwt.is_evm_stack,
    bwt.is_solana,
    bwt.ecosystem_count,
    bwt.is_in_ossd,
    bwt.is_owner_in_ossd
  FROM base_with_metrics_and_times AS bwt
  LEFT JOIN packages_agg AS rp
    ON bwt.artifact_id = rp.artifact_id
  LEFT JOIN github_users_filtered AS gu
    ON bwt.artifact_namespace = gu.artifact_name
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
