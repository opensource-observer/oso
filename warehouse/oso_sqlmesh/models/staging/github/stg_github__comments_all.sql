MODEL (
  name oso.stg_github__comments_all,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 90,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  dialect "duckdb",
  start @github_incremental_start,
  partitioned_by DAY(event_time),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := event_time,
      no_gap_date_part := 'day',
    ),
  )
);

SELECT * FROM oso.stg_github__comments
UNION ALL
SELECT * FROM oso.stg_github__comments_since_20251007
