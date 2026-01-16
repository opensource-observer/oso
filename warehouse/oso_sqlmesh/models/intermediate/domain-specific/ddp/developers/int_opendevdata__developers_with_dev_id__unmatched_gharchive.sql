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
WHERE NOT EXISTS (
  SELECT 1
  FROM oso.int_opendevdata__developers AS odd
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
