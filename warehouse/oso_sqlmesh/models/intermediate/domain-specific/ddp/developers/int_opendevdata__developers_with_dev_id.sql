MODEL (
  name oso.int_opendevdata__developers_with_dev_id,
  description 'Association between GitHub developers and OpenDevData canonical developers based on name, email and time',
  dialect trino,
  kind FULL,
  partitioned_by DAY("valid_from"),
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
  gh.actor_id,
  gh.actor_login,
  COALESCE(gh.author_name, odd.author_name) AS author_name,
  COALESCE(gh.author_email, odd.author_email) AS author_email,
  odd.canonical_developer_id,
  odd.primary_github_user_id,
  CASE
    WHEN gh.valid_from IS NULL THEN odd.valid_from
    WHEN odd.valid_from IS NULL THEN gh.valid_from
    ELSE GREATEST(gh.valid_from, odd.valid_from)
  END AS valid_from,
  CASE
    WHEN gh.valid_to IS NULL AND odd.valid_to IS NULL THEN NULL
    WHEN gh.valid_to IS NULL THEN odd.valid_to
    WHEN odd.valid_to IS NULL THEN gh.valid_to
    ELSE LEAST(gh.valid_to, odd.valid_to)
  END AS valid_to
FROM oso.int_gharchive__developers AS gh
FULL JOIN oso.int_opendevdata__developers AS odd
  ON gh.author_name = odd.author_name
  AND gh.author_email = odd.hashed_author_email
  AND (
    (gh.valid_to IS NULL OR gh.valid_to > odd.valid_from)
    AND (odd.valid_to IS NULL OR odd.valid_to > gh.valid_from)
  )
