MODEL (
  name oso.int_ddp_repositories_consolidated,
  description 'Consolidated repository data from gharchive, opendevdata, and ossd sources with temporal validity',
  dialect trino,
  kind FULL,
  grain (repo_id, repo_name, valid_from),
  tags (
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Get all name variants from gharchive (including historical names) with temporal validity
WITH gharchive_all_names AS (
  SELECT
    repo_id,
    repo_name,
    valid_from,
    valid_to
  FROM oso.int_gharchive__repositories
),
-- Get current name per repo_id from gharchive
gharchive_current AS (
  SELECT
    repo_id,
    repo_name AS current_repo_name
  FROM gharchive_all_names
  WHERE valid_to IS NULL
),
-- Get most recent name per repo_id from gharchive for fallback matching
gharchive_for_matching AS (
  SELECT
    repo_id,
    repo_name,
    ROW_NUMBER() OVER (
      PARTITION BY repo_id
      ORDER BY valid_from DESC
    ) AS rn
  FROM gharchive_all_names
),
-- Standardize ossd data
ossd_standardized AS (
  SELECT
    id AS repo_id,
    name_with_owner AS repo_name,
    node_id AS github_graphql_id,
    NULL AS opendevdata_id,
    star_count,
    fork_count,
    created_at AS repo_created_at,
    is_fork,
    language,
    NULL AS is_opendevdata_blacklist,
    2 AS source_priority
  FROM oso.stg_ossd__current_repositories
),
-- Standardize opendevdata data (using enriched model with repo_id)
opendevdata_standardized AS (
  SELECT
    repo_id,
    repo_name,
    github_graphql_id,
    opendevdata_id,
    star_count,
    fork_count,
    repo_created_at,
    NULL AS is_fork,
    NULL AS language,
    is_opendevdata_blacklist,
    1 AS source_priority
  FROM oso.int_opendevdata__repositories_with_repo_id
),
-- Get canonical repository metadata per repo_id (prioritizing opendevdata > ossd > gharchive)
canonical_repo_data AS (
  SELECT
    repo_id,
    github_graphql_id,
    opendevdata_id,
    star_count,
    fork_count,
    repo_created_at,
    is_fork,
    language,
    is_opendevdata_blacklist,
    source_priority,
    ROW_NUMBER() OVER (
      PARTITION BY repo_id
      ORDER BY source_priority ASC
    ) AS rn
  FROM (
    SELECT
      repo_id,
      github_graphql_id,
      opendevdata_id,
      star_count,
      fork_count,
      repo_created_at,
      is_fork,
      language,
      is_opendevdata_blacklist,
      1 AS source_priority  -- opendevdata
    FROM opendevdata_standardized
    WHERE repo_id IS NOT NULL
    UNION ALL
    SELECT
      repo_id,
      github_graphql_id,
      opendevdata_id,
      star_count,
      fork_count,
      repo_created_at,
      is_fork,
      language,
      is_opendevdata_blacklist,
      2 AS source_priority  -- ossd
    FROM ossd_standardized
    WHERE repo_id IS NOT NULL
    UNION ALL
    SELECT
      repo_id,
      NULL AS github_graphql_id,
      NULL AS opendevdata_id,
      NULL AS star_count,
      NULL AS fork_count,
      NULL AS repo_created_at,
      NULL AS is_fork,
      NULL AS language,
      NULL AS is_opendevdata_blacklist,
      3 AS source_priority  -- gharchive (fallback, no metadata)
    FROM gharchive_for_matching
    WHERE rn = 1
      AND repo_id IS NOT NULL
  ) canonical_sources
),
canonical_data AS (
  SELECT
    repo_id,
    github_graphql_id,
    opendevdata_id,
    star_count,
    fork_count,
    repo_created_at,
    is_fork,
    language,
    is_opendevdata_blacklist
  FROM canonical_repo_data
  WHERE rn = 1
),
-- Collect all (repo_id, repo_name, valid_from, valid_to) from all sources
-- gharchive has temporal data; ossd/opendevdata only used if repo not in gharchive
all_repo_names_temporal AS (
  -- gharchive names with temporal validity (primary source)
  SELECT
    repo_id,
    repo_name,
    valid_from,
    valid_to
  FROM gharchive_all_names
  WHERE repo_id IS NOT NULL
  UNION
  -- ossd names ONLY if repo not in gharchive
  SELECT
    ossd.repo_id,
    ossd.repo_name,
    COALESCE(ossd.repo_created_at, TIMESTAMP '1970-01-01 00:00:00') AS valid_from,
    NULL AS valid_to
  FROM ossd_standardized AS ossd
  WHERE ossd.repo_id IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM gharchive_all_names AS gh WHERE gh.repo_id = ossd.repo_id
    )
  UNION
  -- opendevdata names ONLY if repo not in gharchive or ossd
  SELECT
    odd.repo_id,
    odd.repo_name,
    COALESCE(odd.repo_created_at, TIMESTAMP '1970-01-01 00:00:00') AS valid_from,
    NULL AS valid_to
  FROM opendevdata_standardized AS odd
  WHERE odd.repo_id IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM gharchive_all_names AS gh WHERE gh.repo_id = odd.repo_id
    )
    AND NOT EXISTS (
      SELECT 1 FROM ossd_standardized AS ossd WHERE ossd.repo_id = odd.repo_id
    )
),
-- Get current name for each repo_id (from gharchive if available, else from ossd/opendevdata)
current_names AS (
  SELECT
    repo_id,
    current_repo_name
  FROM gharchive_current
  UNION
  -- For repos not in gharchive, use ossd name as current
  SELECT
    ossd.repo_id,
    ossd.repo_name AS current_repo_name
  FROM ossd_standardized AS ossd
  WHERE ossd.repo_id IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM gharchive_current AS gc WHERE gc.repo_id = ossd.repo_id
    )
  UNION
  -- For repos not in gharchive or ossd, use opendevdata name as current
  SELECT
    odd.repo_id,
    odd.repo_name AS current_repo_name
  FROM opendevdata_standardized AS odd
  WHERE odd.repo_id IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM gharchive_current AS gc WHERE gc.repo_id = odd.repo_id
    )
    AND NOT EXISTS (
      SELECT 1 FROM ossd_standardized AS ossd WHERE ossd.repo_id = odd.repo_id
    )
),
-- Deduplicate current names (in case of conflicts, take first)
current_names_deduped AS (
  SELECT
    repo_id,
    current_repo_name,
    ROW_NUMBER() OVER (PARTITION BY repo_id ORDER BY current_repo_name) AS rn
  FROM current_names
)

-- Final output: one row per (repo_id, repo_name, valid_from) with canonical data and current name
SELECT
  art.repo_id,
  art.repo_name,
  cnd.current_repo_name,
  art.valid_from,
  art.valid_to,
  cd.github_graphql_id,
  cd.opendevdata_id,
  cd.star_count,
  cd.fork_count,
  cd.repo_created_at,
  cd.is_fork,
  cd.language,
  cd.is_opendevdata_blacklist
FROM all_repo_names_temporal AS art
LEFT JOIN canonical_data AS cd
  ON art.repo_id = cd.repo_id
LEFT JOIN current_names_deduped AS cnd
  ON art.repo_id = cnd.repo_id
  AND cnd.rn = 1
