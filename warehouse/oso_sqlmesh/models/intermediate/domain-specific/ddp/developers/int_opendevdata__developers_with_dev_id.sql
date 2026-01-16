MODEL (
  name oso.int_opendevdata__developers_with_dev_id,
  description 'Association between GitHub developers and OpenDevData canonical developers. Uses two-pass join strategy: (1) actor_id match when both sides have non-NULL values, (2) name/email fallback when OpenDevData actor_id is NULL. This enables hash joins instead of nested loops.',
  dialect trino,
  kind FULL,
  partitioned_by YEAR("valid_from"),
  grain (actor_id, canonical_developer_id, author_name, author_email, valid_from),
  tags (
    "opendevdata",
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  actor_id,
  actor_login,
  author_name,
  author_email,
  canonical_developer_id,
  primary_github_user_id,
  valid_from,
  valid_to
FROM oso.int_opendevdata__developers_with_dev_id__deduplicated
WHERE rn = 1
