MODEL (
  name oso.int_ddp__commits_unified,
  description 'Unified commits from GHArchive and OpenDevData, joined on SHA. Provides both actor_id (pusher) and author_id (commit author) for each commit. Grain is (sha, repository_id) since the same commit can appear in multiple repos (forks).',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 180,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  grain (sha, repository_id),
  tags (
    "ddp",
    "commits",
    "opendevdata",
    "github"
  ),
  audits (
    not_null(columns := (sha, repository_id)),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day'
    )
  )
);

WITH gha_commits AS (
  SELECT
    sha,
    created_at,
    repository_id,
    repository_name,
    actor_id,
    actor_login,
    author_name,
    author_email
  FROM oso.int_github__commits_all
  WHERE created_at BETWEEN @start_dt AND @end_dt
),
odd_commits_with_repo_mapping AS (
  SELECT
    odc.sha1 AS sha,
    odc.committed_at AS created_at,
    repo_map.repo_id AS repository_id,
    repo_map.repo_name AS repository_name,
    NULL AS actor_id,
    NULL AS actor_login,
    odc.commit_author_name AS author_name,
    odc.commit_author_email AS author_email,
    odc.canonical_developer_id,
    odc.is_bot,
    odc.additions,
    odc.deletions,
    odc.committed_at,
    odc.authored_at
  FROM oso.stg_opendevdata__commits AS odc
  LEFT JOIN oso.int_opendevdata__repositories_with_repo_id AS repo_map
    ON odc.repo_id = repo_map.opendevdata_id
  WHERE odc.committed_at BETWEEN @start_dt AND @end_dt
    AND repo_map.repo_id IS NOT NULL
),
odd_commits_with_dev_info AS (
  SELECT
    odc.*,
    node_map.decoded_id AS author_id,
    devs.primary_github_user_id
  FROM odd_commits_with_repo_mapping odc
  LEFT JOIN oso.stg_opendevdata__canonical_developers AS devs
    ON odc.canonical_developer_id = devs.id
  LEFT JOIN oso.int_github__node_id_map AS node_map
    ON devs.primary_github_user_id = node_map.node_id
),
unified_commits AS (
  SELECT
    g.sha,
    g.created_at,
    g.repository_id,
    g.repository_name,
    g.actor_id,
    g.actor_login,
    g.author_name,
    g.author_email,
    o.canonical_developer_id,
    o.is_bot,
    o.additions,
    o.deletions,
    o.committed_at,
    o.authored_at,
    o.author_id,
    o.primary_github_user_id,
    'gharchive' AS source
  FROM gha_commits g
  LEFT JOIN odd_commits_with_dev_info o
    ON g.sha = o.sha AND g.repository_id = o.repository_id
  UNION ALL
  SELECT
    o.sha,
    o.created_at,
    o.repository_id,
    o.repository_name,
    o.actor_id,
    o.actor_login,
    o.author_name,
    o.author_email,
    o.canonical_developer_id,
    o.is_bot,
    o.additions,
    o.deletions,
    o.committed_at,
    o.authored_at,
    o.author_id,
    o.primary_github_user_id,
    'opendevdata' AS source
  FROM odd_commits_with_dev_info o
  WHERE NOT EXISTS (
    SELECT 1 FROM gha_commits g 
    WHERE g.sha = o.sha AND g.repository_id = o.repository_id
  )
)
SELECT
  sha,
  created_at,
  repository_id,
  repository_name,
  actor_id,
  actor_login,
  author_name,
  author_email,
  canonical_developer_id,
  is_bot,
  additions,
  deletions,
  committed_at,
  authored_at,
  author_id,
  primary_github_user_id,
  source
FROM unified_commits
