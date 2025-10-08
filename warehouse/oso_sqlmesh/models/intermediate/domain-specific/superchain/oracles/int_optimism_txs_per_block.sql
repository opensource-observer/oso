MODEL (
  name oso.int_optimism_txs_per_block,
  description "Optimism transactions per block",
  dialect trino,
  kind incremental_by_time_range(
   time_column block_timestamp,
   batch_size 60,
   batch_concurrency 1,
   lookback 14,
   forward_only true,
  on_destructive_change warn,   
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
  block_timestamp,
  APPROX_DISTINCT(transaction_hash) AS txs_in_block
FROM oso.stg_superchain__transactions
WHERE
  block_timestamp BETWEEN @start_dt AND @end_dt
  AND chain = 'OPTIMISM'
GROUP BY 1
