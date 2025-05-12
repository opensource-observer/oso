MODEL (
  name oso.int_superchain_traces_txs_joined,
  description 'Traces joined on transactions (by hash and chain)',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 31
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx,
    to_address_tx,
    from_address_trace,
    to_address_trace,
    gas_used_tx,
    gas_used_trace,
    gas_price_tx
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
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
  transactions.gas_used AS gas_used_tx,
  traces.gas_used AS gas_used_trace,
  transactions.gas_price AS gas_price_tx
FROM oso.stg_superchain__transactions AS transactions
LEFT JOIN oso.stg_superchain__traces AS traces
  ON transactions.transaction_hash = traces.transaction_hash
  AND transactions.chain = traces.chain
WHERE
  transactions.block_timestamp BETWEEN @start_dt AND @end_dt
  AND traces.block_timestamp BETWEEN @start_dt AND @end_dt