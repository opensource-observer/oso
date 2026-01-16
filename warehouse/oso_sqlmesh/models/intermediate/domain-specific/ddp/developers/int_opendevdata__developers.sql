MODEL (
  name oso.int_opendevdata__developers,
  description 'Developers from OpenDevData commits, tracking canonical developer and author details history with decoded actor_id. Uses pre-computed Node ID mapping for efficient decoding.',
  dialect trino,
  kind FULL,
  partitioned_by YEAR("valid_from"),
  grain (canonical_developer_id, primary_github_user_id, actor_id, author_name, author_email, valid_from),
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
    @decode_github_node_id(devs.primary_github_user_id) AS actor_id,
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
  GROUP BY 1, 2, 3, 4, 5, 6
),
developer_history_with_actor_id AS (
  SELECT
    dh.canonical_developer_id,
    dh.primary_github_user_id,
    node_map.decoded_id AS actor_id,
    dh.author_name,
    dh.author_email,
    dh.hashed_author_email,
    dh.valid_from
  FROM developer_history AS dh
  LEFT JOIN oso.int_github__node_id_map AS node_map
    ON dh.primary_github_user_id = node_map.node_id
),
developer_history_with_valid_to AS (
  SELECT
    canonical_developer_id,
    primary_github_user_id,
    actor_id,
    author_name,
    author_email,
    hashed_author_email,
    valid_from,
    LEAD(valid_from) OVER (
      PARTITION BY canonical_developer_id
      ORDER BY valid_from
    ) AS valid_to
  FROM developer_history_with_actor_id
)

SELECT
  canonical_developer_id,
  primary_github_user_id,
  actor_id,
  author_name,
  author_email,
  hashed_author_email,
  valid_from,
  valid_to
FROM developer_history_with_valid_to
