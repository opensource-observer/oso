MODEL (
  name oso.int_optimism__op_token_activity_by_address,
  kind INCREMENTAL_BY_TIME_RANGE(
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
    on_destructive_change warn
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("block_timestamp"),
  grain(
    block_timestamp,
    address,
    func_bucket
  ),
  audits(
    has_at_least_n_rows(threshold := 0)
  ),
  ignored_rules(
    "incrementalmustdefinenogapsaudit"
  ),
  tags(
    "superchain",
    "incremental",
    "optimism"
  )
);

/*
  Daily address-level OP token activity aggregation.
  
  Summarizes transfer activity by sender address and function category,
  providing transaction counts, value totals, and sample counterparties.
*/

WITH activity AS (
  SELECT
    block_timestamp,
    transaction_hash,
    tx_from_address,
    called_contract,
    op_from_address,
    op_to_address,
    value_op,
    func_name,
    func_bucket
  FROM oso.int_optimism__op_token_activity
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),

address_stats AS (
  SELECT
    DATE_TRUNC('day', block_timestamp) AS block_timestamp,
    op_from_address AS address,
    func_bucket,
    COUNT(*) AS tx_count,
    SUM(value_op) AS total_value,
    AVG(value_op) AS avg_value,
    ARBITRARY(tx_from_address) AS sample_tx_from,
    ARBITRARY(called_contract) AS sample_counterparty
  FROM activity
  WHERE op_from_address IS NOT NULL
  GROUP BY
    DATE_TRUNC('day', block_timestamp),
    op_from_address,
    func_bucket
)

SELECT
  block_timestamp,
  address,
  func_bucket,
  tx_count,
  total_value,
  avg_value,
  sample_tx_from,
  sample_counterparty
FROM address_stats
