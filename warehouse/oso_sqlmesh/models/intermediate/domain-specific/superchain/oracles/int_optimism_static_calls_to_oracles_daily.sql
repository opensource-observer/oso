MODEL (
  name oso.int_optimism_static_calls_to_oracles_daily,
  description "Optimism static calls to oracles daily",
  dialect trino,
  kind incremental_by_time_range(
   time_column bucket_day,
   batch_size 60,
   batch_concurrency 2,
   lookback 31,
   forward_only true,
   on_destructive_change warn,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by MONTH("bucket_day"),
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
);

WITH events AS (
  SELECT
    DATE_TRUNC('DAY', block_timestamp) AS bucket_day,
    project_name,
    from_address_trace,
    to_address_trace,
    to_address_tx,
    gas_used_trace / 1e9 * gas_price_tx AS read_fees,
    gas_used_tx / 1e9 * gas_price_tx AS l2_tx_fees,
    l1_fee / 1e9 AS l1_fees,
    l1_fee / 1e9 / NULLIF(txs_in_block,0) AS adj_l1_fees,
    transaction_hash
  FROM oso.int_optimism_static_calls_to_oracles
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),
gas_math AS (
  SELECT
    *,
    (1-COALESCE(adj_l1_fees/l2_tx_fees,0))*read_fees AS adj_read_fees
  FROM events
),
grouped_events AS (
  SELECT
    bucket_day,
    project_name,
    from_address_trace,
    to_address_trace,
    to_address_tx,
    SUM(read_fees) AS read_op_fees_gwei,
    SUM(adj_read_fees) AS amortized_read_op_fees_gwei,
    SUM(l2_tx_fees) AS l2_tx_fees_gwei,
    SUM(l1_fees) AS l1_fees_gwei,
    SUM(adj_l1_fees) AS amortized_l1_fees_gwei,
    COUNT(DISTINCT transaction_hash) AS transaction_count
  FROM gas_math
  GROUP BY 1, 2, 3, 4, 5
)
SELECT
  bucket_day,
  project_name,
  from_address_trace,
  to_address_trace,
  to_address_tx,
  read_op_fees_gwei,
  amortized_read_op_fees_gwei,
  l2_tx_fees_gwei,
  l1_fees_gwei,
  amortized_l1_fees_gwei,
  transaction_count,
  @oso_entity_id('OPTIMISM', '', from_address_trace) AS from_artifact_id,
  @oso_entity_id('OPTIMISM', '', to_address_tx) AS to_artifact_id
FROM grouped_events