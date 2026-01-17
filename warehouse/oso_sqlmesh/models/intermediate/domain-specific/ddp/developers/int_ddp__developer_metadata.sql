MODEL (
  name oso.int_ddp__developer_metadata,
  description 'Historical developer metadata tracking all emails, names, and logins per user_id. Many-to-one relationship with developers.',
  dialect trino,
  kind FULL,
  partitioned_by bucket(user_id, 32),
  grain (user_id, metadata_type, metadata_value),
  tags (
    "ddp",
    "developers",
    "metadata"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Track three types of metadata per developer:
-- 1. Author identity (name + email) - from commit authorship
-- 2. Actor login - from GHArchive push events
--
-- Each metadata combination is tracked with first/last seen and commit count.

WITH author_metadata AS (
  -- Track author name + email combinations from commits with author_id
  SELECT
    author_id AS user_id,
    'author_identity' AS metadata_type,
    CONCAT(COALESCE(author_name, ''), ':', COALESCE(author_email, '')) AS metadata_value,
    author_name,
    author_email,
    CAST(NULL AS VARCHAR) AS actor_login,
    MIN(created_at) AS first_seen,
    MAX(created_at) AS last_seen,
    COUNT(*) AS commit_count
  FROM oso.int_ddp__commits_unified
  WHERE author_id IS NOT NULL
    AND (author_name IS NOT NULL OR author_email IS NOT NULL)
  GROUP BY 1, 2, 3, 4, 5, 6
),
actor_login_metadata AS (
  -- Track actor login history from all commits
  SELECT
    actor_id AS user_id,
    'actor_login' AS metadata_type,
    actor_login AS metadata_value,
    CAST(NULL AS VARCHAR) AS author_name,
    CAST(NULL AS VARCHAR) AS author_email,
    actor_login,
    MIN(created_at) AS first_seen,
    MAX(created_at) AS last_seen,
    COUNT(*) AS commit_count
  FROM oso.int_ddp__commits_unified
  WHERE actor_id IS NOT NULL
    AND actor_login IS NOT NULL
  GROUP BY 1, 2, 3, 4, 5, 6
)

SELECT
  user_id,
  metadata_type,
  metadata_value,
  author_name,
  author_email,
  actor_login,
  first_seen,
  last_seen,
  commit_count
FROM author_metadata

UNION ALL

SELECT
  user_id,
  metadata_type,
  metadata_value,
  author_name,
  author_email,
  actor_login,
  first_seen,
  last_seen,
  commit_count
FROM actor_login_metadata
