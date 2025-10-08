MODEL (
  name oso.int_optimism_static_calls_to_oracles,
  description "Optimism static calls to oracles",
  dialect trino,
  kind incremental_by_time_range(
   time_column block_timestamp,
   batch_size 60,
   batch_concurrency 2,
   lookback 31,
   forward_only true,
   on_destructive_change warn,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by MONTH("block_timestamp"),
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
  sc.block_timestamp,
  sc.chain,
  sc.transaction_hash,
  sc.from_address_tx,
  sc.to_address_tx,
  sc.from_address_trace,
  sc.to_address_trace,
  sc.trace_address,
  CAST(sc.gas_used_trace AS DOUBLE) AS gas_used_trace,
  CAST(sc.gas_used_tx AS DOUBLE) AS gas_used_tx,
  CAST(sc.gas_price_tx AS DOUBLE) AS gas_price_tx,
  CAST(sc.l1_fee AS DOUBLE) AS l1_fee,
  txs_per_block.txs_in_block,
  oracle_addresses.project_name
FROM oso.int_superchain_static_calls_txs_joined AS sc
JOIN oso.int_optimism_oracle_addresses AS oracle_addresses
  ON oracle_addresses.artifact_name = sc.to_address_trace
JOIN oso.int_optimism_txs_per_block AS txs_per_block
  ON txs_per_block.block_timestamp = sc.block_timestamp
WHERE
  sc.chain = 'OPTIMISM'
  AND sc.block_timestamp BETWEEN @start_dt AND @end_dt