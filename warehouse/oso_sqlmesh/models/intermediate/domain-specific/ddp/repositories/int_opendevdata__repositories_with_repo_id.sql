MODEL (
  name oso.int_opendevdata__repositories_with_repo_id,
  description 'OpenDevData repositories enriched with repo_id from OSSD (via github_graphql_id), Node ID decoding, or gharchive (via repo_name fallback)',
  dialect trino,
  kind FULL,
  grain (opendevdata_id),
  tags (
    "opendevdata",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Match opendevdata to ossd via github_graphql_id and decode node_id
WITH opendevdata_with_graphql_match AS (
  SELECT
    odd.id AS opendevdata_id,
    odd.repo_created_at,
    LOWER(odd.name) AS repo_name,
    odd.github_graphql_id,
    odd.num_stars AS star_count,
    odd.num_forks AS fork_count,
    CAST(odd.is_blacklist = 1 AS BOOLEAN) AS is_opendevdata_blacklist,
    ossd.id AS repo_id_from_graphql,
    @decode_github_node_id(NULLIF(odd.github_graphql_id, '')) AS repo_id_from_node_id
  FROM oso.stg_opendevdata__repos AS odd
  LEFT JOIN oso.stg_ossd__current_repositories AS ossd
    ON NULLIF(odd.github_graphql_id, '') = ossd.node_id
),
-- Identify repo_names that need fallback matching (no graphql match AND no node_id decoding)
opendevdata_needing_fallback AS (
  SELECT DISTINCT repo_name
  FROM opendevdata_with_graphql_match
  WHERE repo_id_from_graphql IS NULL
    AND repo_id_from_node_id IS NULL
),
-- Get most recent name per repo_id from gharchive,
-- for repo_names that need fallback
gharchive_current_names AS (
  SELECT
    ghr.repo_id,
    ghr.repo_name,
    ROW_NUMBER() OVER (
      PARTITION BY ghr.repo_id
      ORDER BY ghr.valid_from DESC
    ) AS rn
  FROM oso.int_gharchive__repositories AS ghr
  INNER JOIN opendevdata_needing_fallback AS onf
    ON ghr.repo_name = onf.repo_name
),

final_output AS (
  SELECT
    ogm.opendevdata_id,
    ogm.repo_created_at,
    ogm.repo_name,
    ogm.github_graphql_id,
    ogm.star_count,
    ogm.fork_count,
    ogm.is_opendevdata_blacklist,
    COALESCE(
      ogm.repo_id_from_graphql,
      ogm.repo_id_from_node_id,
      gh.repo_id
    ) AS repo_id,
    CASE
      WHEN ogm.repo_id_from_graphql IS NOT NULL THEN 'ossd'
      WHEN ogm.repo_id_from_node_id IS NOT NULL THEN 'node_id'
      WHEN gh.repo_id IS NOT NULL THEN 'gharchive'
      ELSE 'opendevdata'
    END AS repo_id_source
  FROM opendevdata_with_graphql_match AS ogm
  LEFT JOIN gharchive_current_names AS gh
    ON ogm.repo_name = gh.repo_name
    AND ogm.repo_id_from_graphql IS NULL
    AND ogm.repo_id_from_node_id IS NULL
    AND gh.rn = 1
)

SELECT
  opendevdata_id,
  github_graphql_id,
  repo_id,
  repo_name,
  star_count,
  fork_count,
  repo_created_at,
  repo_id_source,
  is_opendevdata_blacklist
FROM final_output
