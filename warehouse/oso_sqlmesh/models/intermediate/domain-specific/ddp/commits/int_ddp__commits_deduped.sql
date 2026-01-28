MODEL (
  name oso.int_ddp__commits_deduped,
  description 'Deduplicated commits from int_ddp__commits_unified. Keeps the first occurrence of each (sha, repository_id) pair by created_at. Use this model when you need unique commits per repository.',
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
    "commits"
  ),
  audits (
    not_null(columns := (sha, repository_id)),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day'
    )
  )
);

@DEF(deduplication_window, 180);

WITH ranked_commits AS (
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
    source,
    ROW_NUMBER() OVER (
      PARTITION BY repository_id, sha
      ORDER BY created_at ASC
    ) AS rn
  FROM oso.int_ddp__commits_unified
  WHERE created_at BETWEEN @start_dt - INTERVAL @deduplication_window DAY AND @end_dt
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
FROM ranked_commits
WHERE rn = 1
  AND created_at BETWEEN @start_dt AND @end_dt
