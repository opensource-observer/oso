MODEL (
  name oso.stg_github__pull_request_merge_events_all,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 365,
    batch_concurrency 3,
    lookback 14,
    forward_only true,
  ),
  start @github_incremental_start,
  partitioned_by DAY(event_time),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := event_time,
      no_gap_date_part := 'day',
    ),
  )
);

SELECT * FROM oso.stg_github__pull_request_merge_events
UNION ALL
SELECT * FROM oso.stg_github__pull_request_merge_events_since_20251007
