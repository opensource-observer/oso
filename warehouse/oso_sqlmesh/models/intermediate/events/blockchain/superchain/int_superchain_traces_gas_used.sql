MODEL (
  name oso.int_superchain_traces_gas_used,
  description 'Pre-aggregated gas totals per transaction for efficient trace-level calculations',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
    on_destructive_change warn
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
);

SELECT
  block_timestamp,
  chain,
  transaction_hash,
  SUM(gas_used)::DOUBLE AS total_gas_used
FROM oso.stg_superchain__traces
WHERE block_timestamp BETWEEN @start_dt AND @end_dt
GROUP BY 1, 2, 3
