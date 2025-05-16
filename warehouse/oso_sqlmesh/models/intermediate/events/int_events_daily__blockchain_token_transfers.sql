MODEL (
  name oso.int_events_daily__blockchain_token_transfers,
  description "Intermediate table for daily blockchain token transfers",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@weekly',
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type", "event_source"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);


SELECT
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  event_source::VARCHAR,
  event_type::VARCHAR,
  SUM(amount) AS amount
FROM oso.int_events__blockchain_token_transfers
WHERE time BETWEEN @start_dt AND @end_dt
GROUP BY 1, 2, 3, 4, 5