MODEL (
  name oso.stg_github__distinct_commits_resolved_mergebot,
  description 'Resolve merges that were created by the mergebot',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 7
  ),
  start @github_incremental_start,
  dialect duckdb,
  partitioned_by DAY(created_at),
  audits (
    number_of_rows(threshold := 0)
  )
);

@DEF(merge_lead_window, 90);

WITH merge_bot_commits AS (
  SELECT
    *
  FROM oso.stg_github__distinct_main_commits
  WHERE
    actor_id = 118344674
    and created_at BETWEEN @start_dt AND @end_dt
), resolved_merge_bot_commits AS (
  SELECT
    mbc.repository_id,
    mbc.sha,
    mbc.created_at,
    mbc.repository_name,
    mbc.push_id,
    mbc.ref,
    ghprme.actor_id,
    ghprme.actor_login,
    mbc.author_email,
    mbc.author_name,
    mbc.is_distinct,
    mbc.api_url
  FROM merge_bot_commits AS mbc
  INNER JOIN oso.stg_github__pull_request_merge_events AS ghprme
    ON mbc.repository_id = ghprme.repository_id AND mbc.sha = ghprme.merge_commit_sha
  WHERE ghprme.created_at BETWEEN @start_dt - INTERVAL @merge_lead_window DAY AND @end_dt
), no_merge_bot_commits AS (
  SELECT
    *
  FROM oso.stg_github__distinct_main_commits
  /* The following is the actor_id for the github merge bot */
  WHERE
    actor_id <> 118344674
    and created_at BETWEEN @start_dt AND @end_dt
)
SELECT
  *
FROM resolved_merge_bot_commits
UNION ALL
SELECT
  *
FROM no_merge_bot_commits