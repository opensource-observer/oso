MODEL (
  name oso.int_gharchive__developers,
  description 'Developers (actors) from GitHub Archive commits, tracking login and author details history',
  dialect trino,
  kind FULL,
  partitioned_by MONTH("valid_from"),
  grain (actor_id, actor_login, author_name, author_email, valid_from),
  tags (
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_commits AS (
  SELECT
    actor_id,
    actor_login,
    author_name,
    author_email,
    created_at
  FROM oso.stg_github__commits
  UNION ALL
  SELECT
    actor_id,
    actor_login,
    author_name,
    author_email,
    created_at
  FROM oso.stg_github__commits_since_20251007
),
developer_history AS (
  SELECT
    actor_id,
    actor_login,
    author_name,
    author_email,
    MIN(created_at) AS valid_from
  FROM all_commits
  WHERE actor_id IS NOT NULL
  GROUP BY 1, 2, 3, 4
),
developer_history_with_valid_to AS (
  SELECT
    actor_id,
    actor_login,
    author_name,
    author_email,
    valid_from,
    LEAD(valid_from) OVER (
      PARTITION BY actor_id
      ORDER BY valid_from
    ) AS valid_to
  FROM developer_history
)

SELECT
  actor_id,
  actor_login,
  author_name,
  author_email,
  valid_from,
  valid_to
FROM developer_history_with_valid_to
