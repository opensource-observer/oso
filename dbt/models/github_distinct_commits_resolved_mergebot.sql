{#
  Resolve merges
#}

WITH merge_bot_commits AS (
  SELECT * 
  FROM {{ ref('github_distinct_main_commits') }} 
  WHERE actor_id = 118344674
), resolved_merge_bot_commits AS (
  SELECT 
    mbc.created_at,
    mbc.repository_id,
    mbc.repository_name,
    mbc.push_id,
    mbc.ref,
    ghprme.actor_id,
    ghprme.actor_login,
    mbc.sha,
    mbc.author_email,
    mbc.author_name,
    mbc.is_distinct,
    mbc.api_url
  FROM merge_bot_commits as mbc
  JOIN {{ ref('github_pull_request_merge_events') }} AS ghprme ON mbc.repository_id = ghprme.repository_id AND mbc.sha = ghprme.merge_commit_sha
), no_merge_bot_commits AS (
  SELECT * 
  FROM {{ ref('github_distinct_main_commits') }} 
  WHERE actor_id != 118344674
)
SELECT * FROM resolved_merge_bot_commits
UNION ALL
SELECT * FROM no_merge_bot_commits