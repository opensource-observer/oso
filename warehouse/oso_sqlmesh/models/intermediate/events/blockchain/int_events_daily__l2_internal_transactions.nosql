-- L2 internal transaction events
MODEL (
  name oso.int_events_daily__l2_internal_transactions,
  description 'L2 internal transaction events',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type", "event_source"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
  tags (
    "incremental"
  ),
  enabled false,
);


SELECT
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  is_top_level_transaction,
  APPROX_DISTINCT(transaction_hash) AS "count",
  SUM(l2_gas_fee * share_of_transaction_gas)::DOUBLE AS amortized_l2_gas_fee
FROM oso.int_events__superchain_internal_transactions
WHERE time BETWEEN @start_dt AND @end_dt
GROUP BY 1, 2, 3, 4, 5, 6