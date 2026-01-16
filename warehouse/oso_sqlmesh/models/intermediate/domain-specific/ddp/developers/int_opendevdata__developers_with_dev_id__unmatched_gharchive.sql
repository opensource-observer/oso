MODEL (
  name oso.int_opendevdata__developers_with_dev_id__unmatched_gharchive,
  description 'Unmatched GHArchive developers',
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
  gh.actor_id,
  gh.actor_login,
  gh.author_name,
  gh.author_email,
  CAST(NULL AS BIGINT) AS canonical_developer_id,
  CAST(NULL AS VARCHAR) AS primary_github_user_id,
  gh.valid_from,
  gh.valid_to,
  3 AS match_priority
FROM oso.int_gharchive__developers AS gh
-- Check if matched via actor_id (reuse precomputed matches)
LEFT JOIN oso.int_opendevdata__developers_with_dev_id__actor_id_matches AS m1
  ON gh.actor_id = m1.actor_id
  AND (gh.valid_to IS NULL OR gh.valid_to > m1.valid_from)
  AND (m1.valid_to IS NULL OR m1.valid_to > gh.valid_from)
-- Check if matched via name/email (reuse precomputed matches)
LEFT JOIN oso.int_opendevdata__developers_with_dev_id__name_email_matches AS m2
  ON gh.author_name = m2.author_name
  AND gh.author_email = m2.author_email
  AND (gh.valid_to IS NULL OR gh.valid_to > m2.valid_from)
  AND (m2.valid_to IS NULL OR m2.valid_to > gh.valid_from)
-- Keep only rows that didn't match either way
WHERE m1.actor_id IS NULL
  AND m2.actor_id IS NULL
