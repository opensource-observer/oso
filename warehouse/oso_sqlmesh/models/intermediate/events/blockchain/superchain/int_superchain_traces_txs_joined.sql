MODEL (
  name oso.int_superchain_traces_txs_joined,
  description 'Traces joined on transactions (by hash and chain)',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  )
);

SELECT
  transactions.block_timestamp,
  transactions.chain AS chain,
  transactions.transaction_hash,
  transactions.from_address AS from_address_tx,
  transactions.to_address AS to_address_tx,
  traces.from_address AS from_address_trace,
  traces.to_address AS to_address_trace,
  traces.gas_used AS gas_used_trace,
  transactions.receipt_gas_used AS gas_used_tx,
  transactions.receipt_effective_gas_price AS gas_price_tx
FROM oso.stg_superchain__traces AS traces
JOIN oso.stg_superchain__transactions AS transactions
  ON transactions.transaction_hash = traces.transaction_hash
  AND transactions.chain = traces.chain
WHERE
  transactions.block_timestamp BETWEEN @start_dt AND @end_dt
  AND traces.block_timestamp BETWEEN @start_dt AND @end_dt
  AND transactions.receipt_status = 1