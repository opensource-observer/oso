MODEL (
  name oso.int_github__events_enriched_with_opendevdata_commits,
  description 'GitHub events enriched with OpenDevData repository and commit information',
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
  tags (
    "opendevdata",
    "ddp",
    "events"
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day'
    )
  )
);

SELECT
  ghe.type,
  ghe.public,
  ghe.payload,
  ghe.repo,
  ghe.actor,
  ghe.org,
  ghe.created_at,
  ghe.id,
  ghe.other,
  ghe.repo.id AS repo_id,
  repos.opendevdata_id AS opendevdata_repo_id,
  repos.github_graphql_id AS ossd_id,
  commits.canonical_developer_id AS commit_canonical_developer_id,
  commits.additions AS commit_additions,
  commits.deletions AS commit_deletions
FROM oso.stg_github__events AS ghe
LEFT JOIN oso.int_opendevdata__repositories_with_repo_id AS repos
  ON ghe.repo.id = repos.repo_id
LEFT JOIN oso.stg_opendevdata__commits AS commits
  ON ghe.type = 'PushEvent'
  AND JSON_EXTRACT_SCALAR(ghe.payload, '$.head') = commits.sha1
  AND repos.opendevdata_id = commits.repo_id
WHERE
  ghe.created_at BETWEEN @start_dt AND @end_dt
