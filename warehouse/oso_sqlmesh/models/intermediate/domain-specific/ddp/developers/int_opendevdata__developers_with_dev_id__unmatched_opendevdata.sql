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
WHERE NOT EXISTS (
  SELECT 1
  FROM oso.int_gharchive__developers AS gh
  WHERE (
    (gh.actor_id = odd.actor_id AND odd.actor_id IS NOT NULL)
    OR (
      odd.actor_id IS NULL
      AND gh.author_name = odd.author_name
      AND gh.author_email = odd.hashed_author_email
      AND gh.author_name IS NOT NULL
      AND gh.author_email IS NOT NULL
      AND odd.author_name IS NOT NULL
      AND odd.hashed_author_email IS NOT NULL
    )
  )
  AND (gh.valid_to IS NULL OR gh.valid_to > odd.valid_from)
  AND (odd.valid_to IS NULL OR odd.valid_to > gh.valid_from)
)
