MODEL (
  name oso.int_opendevdata__developers_with_dev_id__actor_id_matches,
  description 'Actor ID matches for developers',
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
  COALESCE(gh.author_name, odd.author_name) AS author_name,
  COALESCE(gh.author_email, odd.author_email) AS author_email,
  odd.canonical_developer_id,
  odd.primary_github_user_id,
  GREATEST(gh.valid_from, odd.valid_from) AS valid_from,
  CASE
    WHEN gh.valid_to IS NULL AND odd.valid_to IS NULL THEN NULL
    WHEN gh.valid_to IS NULL THEN odd.valid_to
    WHEN odd.valid_to IS NULL THEN gh.valid_to
    ELSE LEAST(gh.valid_to, odd.valid_to)
  END AS valid_to,
  1 AS match_priority
FROM oso.int_gharchive__developers AS gh
INNER JOIN oso.int_opendevdata__developers AS odd
  ON gh.actor_id = odd.actor_id
  AND odd.actor_id IS NOT NULL
  AND (gh.valid_to IS NULL OR gh.valid_to > odd.valid_from)
  AND (odd.valid_to IS NULL OR odd.valid_to > gh.valid_from)
