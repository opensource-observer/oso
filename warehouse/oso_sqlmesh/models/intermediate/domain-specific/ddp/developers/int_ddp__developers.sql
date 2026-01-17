MODEL (
  name oso.int_ddp__developers,
  description 'Unified developers from commits: union of authors (author_id) and actors (actor_id). user_id is the primary identifier (GitHub database ID).',
  dialect trino,
  kind FULL,
  partitioned_by bucket(user_id, 8),
  grain (user_id),
  tags (
    "ddp",
    "developers",
    "opendevdata",
    "github"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Union of:
-- 1. Authors (from commits with canonical_developer_id) - these have richer metadata
-- 2. Actors (pushers from GHArchive) - may not have canonical_developer_id
--
-- When a user appears as both author and actor, we prefer the author record
-- because it has canonical_developer_id and primary_github_user_id.

WITH authors AS (
  -- Distinct authors from unified commits (those with author_id)
  SELECT DISTINCT
    author_id AS user_id,
    canonical_developer_id,
    primary_github_user_id,
    is_bot
  FROM oso.int_ddp__commits_unified
  WHERE author_id IS NOT NULL
),
actors AS (
  -- Distinct actors from unified commits
  SELECT DISTINCT
    actor_id AS user_id,
    CAST(NULL AS BIGINT) AS canonical_developer_id,
    CAST(NULL AS VARCHAR) AS primary_github_user_id,
    CAST(NULL AS BIGINT) AS is_bot
  FROM oso.int_ddp__commits_unified
  WHERE actor_id IS NOT NULL
),
combined AS (
  SELECT * FROM authors
  UNION ALL
  SELECT * FROM actors
),
-- Deduplicate by user_id, preferring records with canonical_developer_id
deduplicated AS (
  SELECT
    user_id,
    canonical_developer_id,
    primary_github_user_id,
    is_bot,
    ROW_NUMBER() OVER (
      PARTITION BY user_id
      ORDER BY
        CASE WHEN canonical_developer_id IS NOT NULL THEN 0 ELSE 1 END,
        canonical_developer_id NULLS LAST
    ) AS rn
  FROM combined
)

SELECT
  user_id,
  canonical_developer_id,
  primary_github_user_id,
  COALESCE(is_bot, 0) AS is_bot
FROM deduplicated
WHERE rn = 1
