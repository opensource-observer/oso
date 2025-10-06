MODEL (
  name oso.int_optimism_oracle_events,
  description "Optimism oracle events",
  dialect trino,
  kind incremental_by_time_range(
   time_column block_timestamp,
   batch_size 60,
   batch_concurrency 2,
   lookback 31,
   forward_only true,
  ),
  start '2024-09-01',
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
  sc.gas_used_trace,
  sc.gas_used_tx,
  sc.gas_price_tx,
  oracle_addresses.project_name,
  'STATIC_CALL' AS event_type
FROM oso.int_superchain_static_calls_txs_joined AS sc
JOIN oso.int_optimism_oracle_addresses AS oracle_addresses
  ON oracle_addresses.artifact_name = sc.to_address_trace
WHERE
  sc.chain = 'OPTIMISM'
  AND sc.block_timestamp BETWEEN @start_dt AND @end_dt
  
UNION ALL

SELECT
  t.block_timestamp,
  t.chain,
  t.transaction_hash,
  t.from_address_tx,
  t.to_address_tx,
  t.from_address_trace,
  t.to_address_trace,
  t.gas_used_trace,
  t.gas_used_tx,
  t.gas_price_tx,
  oracle_addresses.project_name,
  'INTERNAL_CALL' AS event_type
FROM oso.int_superchain_traces_txs_joined AS t
JOIN oso.int_optimism_oracle_addresses AS oracle_addresses
  ON oracle_addresses.artifact_name = t.to_address_trace
WHERE
  t.chain = 'OPTIMISM'
  AND t.block_timestamp BETWEEN @start_dt AND @end_dt