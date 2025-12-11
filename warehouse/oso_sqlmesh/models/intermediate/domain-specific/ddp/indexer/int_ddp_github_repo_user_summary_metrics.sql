MODEL (
  name oso.int_ddp_github_repo_user_summary_metrics,
  description 'Summary metrics for GitHub events by repository and user from GitHub Archive since 2025-01-01',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  partitioned_by ("event_type"),
  grain (repo_id, repo_name, actor_id, actor_login, event_type),
  tags (
    "github",
    "ddp",
  )
);

WITH repos_with_code AS (
  SELECT
    repo_id,
    COUNT(DISTINCT actor_id) AS code_contributor_count
  FROM oso.int_ddp_github_events_daily
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY 1
  HAVING code_contributor_count > 1
),

repo_user_summary AS (
  SELECT
    e.repo_id,
    e.repo_name,
    e.actor_id,
    e.actor_login,
    e.event_type,
    MIN(e.bucket_day) AS first_event_date,
    MAX(e.bucket_day) AS last_event_date,
    COUNT(DISTINCT e.bucket_day) AS total_days_with_activity,
    SUM(e.amount) AS total_events
  FROM oso.int_ddp_github_events_daily AS e
  INNER JOIN repos_with_code AS rc
    ON e.repo_id = rc.repo_id
  GROUP BY 1, 2, 3, 4, 5
)
SELECT
  repo_id,
  repo_name,  
  actor_id,
  actor_login,
  event_type,
  first_event_date,
  last_event_date,
  total_days_with_activity,
  total_events,
  SPLIT_PART(repo_name, '/', 1) = actor_login AS is_maintainer
FROM repo_user_summary