MODEL (
  name oso.int_ddp__commits_unified,
  description 'Unified commits from GHArchive and OpenDevData, joined on SHA. Provides both actor_id (pusher) and author_id (commit author) for each commit.',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  grain (sha),
  tags (
    "ddp",
    "commits",
    "opendevdata",
    "github"
  ),
  audits (
    not_null(columns := (sha,)),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day'
    )
  )
);

-- Merge GHArchive and OpenDevData commits on SHA.
-- GHArchive provides: actor_id (pusher), actor_login, repository_id
-- OpenDevData provides: canonical_developer_id (author identity), additions, deletions
-- We derive author_id by decoding the primary_github_user_id from canonical_devs.
SELECT
  ghc.sha,
  ghc.created_at,
  ghc.repository_id,
  ghc.repository_name,
  ghc.actor_id,
  ghc.actor_login,
  ghc.author_name,
  ghc.author_email,
  odc.canonical_developer_id,
  odc.is_bot,
  odc.additions,
  odc.deletions,
  odc.committed_at,
  odc.authored_at,
  -- Derive author_id from canonical_developer_id via the node_id_map
  -- author_id is the database ID of the commit author (distinct from actor_id which is the pusher)
  node_map.decoded_id AS author_id,
  devs.primary_github_user_id
FROM oso.int_github__commits_all AS ghc
LEFT JOIN oso.stg_opendevdata__commits AS odc
  ON ghc.sha = odc.sha1
LEFT JOIN oso.stg_opendevdata__canonical_developers AS devs
  ON odc.canonical_developer_id = devs.id
LEFT JOIN oso.int_github__node_id_map AS node_map
  ON devs.primary_github_user_id = node_map.node_id
WHERE ghc.created_at BETWEEN @start_dt AND @end_dt
