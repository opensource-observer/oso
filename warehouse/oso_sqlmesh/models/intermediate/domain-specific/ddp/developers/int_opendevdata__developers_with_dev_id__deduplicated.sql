MODEL (
  name oso.int_opendevdata__developers_with_dev_id__deduplicated,
  description 'Deduped combined developer matches from GHArchive and OpenDevData',
  dialect trino,
  kind FULL,
  partitioned_by YEAR("valid_from"),
  tags (
    "opendevdata",
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Prefer actor_id match over name/email match
SELECT
  actor_id,
  actor_login,
  author_name,
  author_email,
  canonical_developer_id,
  primary_github_user_id,
  valid_from,
  valid_to,
  ROW_NUMBER() OVER (
    PARTITION BY
      COALESCE(actor_id, canonical_developer_id),
      author_name,
      author_email,
      valid_from
    ORDER BY match_priority
  ) AS rn
FROM oso.int_opendevdata__developers_with_dev_id__combined AS combined