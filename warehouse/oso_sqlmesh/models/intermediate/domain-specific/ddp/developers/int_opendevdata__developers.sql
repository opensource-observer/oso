MODEL (
  name oso.int_opendevdata__developers,
  description 'Distinct developers from OpenDevData commits. One row per canonical_developer_id with decoded actor_id. Metadata history tracked separately in int_ddp__developer_metadata.',
  dialect trino,
  kind FULL,
  partitioned_by bucket(actor_id, 32),
  grain (canonical_developer_id),
  tags (
    "opendevdata",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ranked_developers AS (
  SELECT
    commits.canonical_developer_id,
    devs.primary_github_user_id,
    node_map.decoded_id AS actor_id,
    commits.commit_author_name AS author_name,
    commits.commit_author_email AS author_email,
    commits.committed_at,
    ROW_NUMBER() OVER (
      PARTITION BY commits.canonical_developer_id
      ORDER BY commits.committed_at DESC
    ) AS rn
  FROM oso.stg_opendevdata__commits AS commits
  INNER JOIN oso.stg_opendevdata__canonical_developers AS devs
    ON commits.canonical_developer_id = devs.id
  LEFT JOIN oso.int_github__node_id_map AS node_map
    ON devs.primary_github_user_id = node_map.node_id
  WHERE commits.canonical_developer_id IS NOT NULL
)

SELECT
  canonical_developer_id,
  primary_github_user_id,
  actor_id,
  author_name,
  author_email,
  @oso_id(author_name, author_email) AS author_synthetic_id
FROM ranked_developers
WHERE rn = 1
