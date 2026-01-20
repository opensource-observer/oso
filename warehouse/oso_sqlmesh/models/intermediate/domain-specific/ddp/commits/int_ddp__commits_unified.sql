MODEL (
  name oso.int_ddp__commits_unified,
  description 'Unified commits from GHArchive and OpenDevData, joined on SHA. Provides both actor_id (pusher) and author_id (commit author) for each commit. Grain is (sha, repository_id) since the same commit can appear in multiple repos (forks).',
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
  grain (sha, repository_id),
  tags (
    "ddp",
    "commits",
    "opendevdata",
    "github"
  ),
  audits (
    not_null(columns := (sha, repository_id)),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day'
    )
  )
);

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
