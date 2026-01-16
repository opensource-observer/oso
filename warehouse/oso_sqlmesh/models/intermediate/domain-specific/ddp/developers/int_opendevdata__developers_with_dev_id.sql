MODEL (
  name oso.int_opendevdata__developers_with_dev_id,
  description 'Association between GitHub developers and OpenDevData canonical developers. Uses two-pass join strategy: (1) actor_id match when both sides have non-NULL values, (2) name/email fallback when OpenDevData actor_id is NULL. This enables hash joins instead of nested loops.',
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

WITH actor_id_matches AS (
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
),

name_email_matches AS (
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
    2 AS match_priority
  FROM oso.int_gharchive__developers AS gh
  INNER JOIN oso.int_opendevdata__developers AS odd
    ON gh.author_name = odd.author_name
    AND gh.author_email = odd.hashed_author_email
    AND odd.actor_id IS NULL
    AND gh.author_name IS NOT NULL
    AND gh.author_email IS NOT NULL
    AND odd.author_name IS NOT NULL
    AND odd.hashed_author_email IS NOT NULL
    AND (gh.valid_to IS NULL OR gh.valid_to > odd.valid_from)
    AND (odd.valid_to IS NULL OR odd.valid_to > gh.valid_from)
),

unmatched_gharchive AS (
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
),

unmatched_opendevdata AS (
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
),

combined AS (
  SELECT * FROM actor_id_matches
  UNION ALL
  SELECT * FROM name_email_matches
  UNION ALL
  SELECT * FROM unmatched_gharchive
  UNION ALL
  SELECT * FROM unmatched_opendevdata
),

-- Deduplicate: prefer actor_id match over name/email match
deduplicated AS (
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
  FROM combined
)

SELECT
  actor_id,
  actor_login,
  author_name,
  author_email,
  canonical_developer_id,
  primary_github_user_id,
  valid_from,
  valid_to
FROM deduplicated
WHERE rn = 1
