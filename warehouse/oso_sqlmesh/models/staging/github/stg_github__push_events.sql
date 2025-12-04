MODEL (
  name oso.stg_github__push_events,
  description 'Gathers all github events for all github artifacts',
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
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

SELECT * FROM oso.stg_github__push_events_v1
UNION ALL
SELECT * FROM oso.stg_github__push_events_v2
