MODEL (
  name oso.int_optimism_oracles_direct_fees_daily,
  description "Optimism oracles direct fees daily",
  dialect trino,
  kind incremental_by_time_range(
   time_column bucket_day,
   batch_size 60,
   batch_concurrency 1,
   lookback 14,
   forward_only true,
   on_destructive_change warn,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by MONTH("bucket_day"),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
    "incrementalmusthaveforwardonly",
  ),
);

WITH events AS (
  SELECT
    DATE_TRUNC('DAY', block_timestamp) AS bucket_day,
    project_name AS oracle_name,
    to_address_trace AS oracle_address,
    gas_used_trace::DOUBLE / 1e18 * gas_price_tx::DOUBLE AS read_fees,
    transaction_hash
  FROM oso.int_optimism_static_calls_to_oracles
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),

addresses_per_txn AS (
  SELECT
    transaction_hash,
    COUNT(DISTINCT oracle_address) AS num_addresses
  FROM events
  GROUP BY 1
),

SELECT
  bucket_day,
  oracle_name,
  oracle_address,
  SUM(read_fees) AS read_fees,
  SUM(1.0 / num_addresses) AS transaction_count
FROM events
JOIN addresses_per_txn
  ON events.transaction_hash = addresses_per_txn.transaction_hash
GROUP BY 1, 2, 3
ORDER BY 1, 2