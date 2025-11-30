MODEL (
  name oso.int_ddp_repo_features,
  description "Developer Data Program repositories with features for clustering analysis",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH base_metadata AS (
  SELECT
    artifact_id,
    artifact_namespace,
    artifact_name,
    artifact_url,
    is_fork,
    created_at,
    updated_at,
    star_count,
    fork_count,
    language,
    is_ethereum,
    is_evm_l1,
    is_evm_l2,
    is_evm_stack,
    is_solana,
    ecosystem_count,
    is_in_ossd,
    is_owner_in_ossd,
    COUNT(*) OVER (PARTITION BY artifact_namespace) AS num_repos_owned_by_maintainer
  FROM oso.int_ddp_repo_metadata
),

pivoted_metrics AS (
  SELECT
    artifact_id,
    MAX(CASE WHEN metric_model = 'contributors' THEN metric_amount END) AS contributor_count,
    MAX(CASE WHEN metric_model = 'commits' THEN metric_amount END) AS commit_count,
    MAX(CASE WHEN metric_model = 'forks' THEN metric_amount END) AS fork_count,
    MAX(CASE WHEN metric_model = 'stars' THEN metric_amount END) AS star_count,
    MAX(CASE WHEN metric_model = 'opened_issues' THEN metric_amount END) AS opened_issue_count,
    MAX(CASE WHEN metric_model = 'closed_issues' THEN metric_amount END) AS closed_issue_count,
    MAX(CASE WHEN metric_model = 'opened_pull_requests' THEN metric_amount END) AS opened_pull_request_count,
    MAX(CASE WHEN metric_model = 'merged_pull_requests' THEN metric_amount END) AS merged_pull_request_count,
    MAX(CASE WHEN metric_model = 'releases' THEN metric_amount END) AS release_count,
    MAX(CASE WHEN metric_model = 'comments' THEN metric_amount END) AS comment_count
  FROM oso.int_ddp_repo_metrics
  GROUP BY artifact_id
),

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
    COALESCE(bm.created_at, ct.first_commit) AS first_activity_time,
    COALESCE(bm.updated_at, ct.last_commit) AS last_activity_time,
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
  LEFT JOIN oso.int_ddp_repo_lineage AS lin
    ON bm.artifact_id = lin.artifact_id
  LEFT JOIN oso.int_first_last_commit_to_github_repository AS ct
    ON bm.artifact_id = ct.artifact_id
  LEFT JOIN pivoted_metrics AS pm
    ON bm.artifact_id = pm.artifact_id
  LEFT JOIN (
    SELECT
      package_owner_artifact_id AS artifact_id,
      COUNT(DISTINCT package_artifact_id) AS package_count,
      CAST(TRUE AS BOOLEAN) AS has_packages
    FROM oso.int_packages__current_maintainer_only
    GROUP BY package_owner_artifact_id
  ) AS rp
    ON bm.artifact_id = rp.artifact_id
  LEFT JOIN oso.int_github_users AS gu
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
