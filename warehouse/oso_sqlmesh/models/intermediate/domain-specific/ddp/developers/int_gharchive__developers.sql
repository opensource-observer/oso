MODEL (
  name oso.int_gharchive__developers,
  description 'Distinct developers (actors) from GitHub Archive commits. One row per actor_id with most recent metadata. Metadata history tracked separately in int_ddp__developer_metadata.',
  dialect trino,
  kind FULL,
  partitioned_by bucket(actor_id, 32),
  grain (actor_id),
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
ranked_developers AS (
  SELECT
    actor_id,
    actor_login,
    author_name,
    author_email,
    created_at,
    ROW_NUMBER() OVER (
      PARTITION BY actor_id
      ORDER BY created_at DESC
    ) AS rn
  FROM all_commits
  WHERE actor_id IS NOT NULL
)

SELECT
  actor_id,
  actor_login,
  author_name,
  author_email,
  @oso_id(author_name, author_email) AS author_synthetic_id
FROM ranked_developers
WHERE rn = 1
