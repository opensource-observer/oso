MODEL (
  name oso.int_opendevdata__developers_with_dev_id__unmatched_opendevdata,
  description 'Unmatched OpenDevData developers',
  dialect trino,
  kind FULL,
  partitioned_by MONTH("valid_from"),
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
  odd.actor_id,
  CAST(NULL AS VARCHAR) AS actor_login,
  odd.author_name,
  odd.author_email,
  odd.canonical_developer_id,
  odd.primary_github_user_id,
  odd.valid_from,
  odd.valid_to,
  4 AS match_priority
FROM oso.int_opendevdata__developers AS odd
-- Check if matched via actor_id (reuse precomputed matches)
LEFT JOIN oso.int_opendevdata__developers_with_dev_id__actor_id_matches AS m1
  ON odd.canonical_developer_id = m1.canonical_developer_id
  AND (odd.valid_to IS NULL OR odd.valid_to > m1.valid_from)
  AND (m1.valid_to IS NULL OR m1.valid_to > odd.valid_from)
-- Check if matched via name/email (reuse precomputed matches)
LEFT JOIN oso.int_opendevdata__developers_with_dev_id__name_email_matches AS m2
  ON odd.canonical_developer_id = m2.canonical_developer_id
  AND (odd.valid_to IS NULL OR odd.valid_to > m2.valid_from)
  AND (m2.valid_to IS NULL OR m2.valid_to > odd.valid_from)
-- Keep only rows that didn't match either way
WHERE m1.canonical_developer_id IS NULL
  AND m2.canonical_developer_id IS NULL
