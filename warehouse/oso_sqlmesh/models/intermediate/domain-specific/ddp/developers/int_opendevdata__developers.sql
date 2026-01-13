MODEL (
  name oso.int_opendevdata__developers,
  description 'Developers from OpenDevData commits, tracking canonical developer and author details history',
  dialect trino,
  kind FULL,
  partitioned_by DAY("valid_from"),
  grain (canonical_developer_id, primary_github_user_id, author_name, author_email, valid_from),
  tags (
    "opendevdata",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH developer_history AS (
  SELECT
    commits.canonical_developer_id,
    devs.primary_github_user_id,
    commits.commit_author_name AS author_name,
    commits.commit_author_email AS author_email,
    CONCAT(
      @sha1_hex(SPLIT_PART(commits.commit_author_email, '@', 1)),
      '@',
      SPLIT_PART(commits.commit_author_email, '@', 2)
    ) AS hashed_author_email,
    MIN(commits.committed_at) AS valid_from
  FROM oso.stg_opendevdata__commits AS commits
  INNER JOIN oso.stg_opendevdata__canonical_developers AS devs
    ON commits.canonical_developer_id = devs.id
  WHERE commits.canonical_developer_id IS NOT NULL
  GROUP BY 1, 2, 3, 4, 5
),
developer_history_with_valid_to AS (
  SELECT
    canonical_developer_id,
    primary_github_user_id,
    author_name,
    author_email,
    hashed_author_email,
    valid_from,
    LEAD(valid_from) OVER (
      PARTITION BY canonical_developer_id
      ORDER BY valid_from
    ) AS valid_to
  FROM developer_history
)

SELECT
  canonical_developer_id,
  primary_github_user_id,
  author_name,
  author_email,
  hashed_author_email,
  valid_from,
  valid_to
FROM developer_history_with_valid_to
