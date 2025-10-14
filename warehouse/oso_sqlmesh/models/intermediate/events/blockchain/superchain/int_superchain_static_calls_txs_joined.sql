MODEL (
  name oso.int_superchain_static_calls_txs_joined,
  description 'Static calls joined on transactions (by hash and chain)',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash, from_address_tx, from_address_trace, to_address_tx, to_address_trace, trace_address),
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
  tx.block_timestamp,
  tx.chain,
  sc.transaction_hash,
  tx.from_address AS from_address_tx,
  tx.to_address AS to_address_tx,
  sc.from_address AS from_address_trace,
  sc.to_address AS to_address_trace,
  sc.gas_used AS gas_used_trace,
  tx.receipt_gas_used AS gas_used_tx,
  tx.receipt_effective_gas_price AS gas_price_tx,
  tx.receipt_l1_fee AS l1_fee,
  sc.trace_address,
  sc.subtraces
FROM oso.stg_superchain__static_calls AS sc
JOIN oso.stg_superchain__transactions AS tx
  ON
    sc.transaction_hash = tx.transaction_hash
    AND sc.chain = tx.chain
WHERE
  sc.block_timestamp BETWEEN @start_dt AND @end_dt
  AND tx.receipt_status = 1
