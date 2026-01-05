MODEL (
  name oso.int_github__commits_all,
  description 'Union of all commits from both historical and new GitHub event schemas',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  dialect trino,
  audits (
    not_null(columns := (sha,)),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

SELECT * FROM oso.stg_github__commits
UNION ALL
SELECT * FROM oso.stg_github__commits_since_20251007
