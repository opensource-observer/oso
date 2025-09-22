MODEL (
  name oso.int_chain_metrics_from_oso_l2_transactions,
  description "Chain-level metrics from OSO L2 transactions",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("sample_date"), "chain", "metric_name"),
  grain (sample_date, chain, metric_name),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
    "incrementalmustdefinenogapsaudit",
  )
);

WITH l2_gas_fees_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    'LAYER2_GAS_FEES' AS metric_name,
    SUM(l2_gas_fee / 1e18) AS amount
  FROM oso.int_events_daily__l2_transactions
  WHERE
    bucket_day BETWEEN @start_dt AND @end_dt
    -- TODO: remove once we have support for custom gas tokens
    AND event_source != 'CELO'
  GROUP BY 1, 2
),

l1_gas_fees_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    'LAYER1_GAS_FEES' AS metric_name,
    SUM(l1_gas_fee / 1e18) AS amount
  FROM oso.int_events_daily__l2_transactions
  WHERE bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

upgrades_7702_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    '7702_EOA_UPGRADES' AS metric_name,
    COUNT(DISTINCT from_artifact_id) AS amount
  FROM oso.int_events_daily__l2_transactions
  WHERE
    transaction_type = 4
    AND to_artifact_id = from_artifact_id
    AND event_type = 'TRANSACTION'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

transaction_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    event_type || 'S' AS metric_name,
    SUM(count) AS amount
  FROM oso.int_events_daily__l2_transactions
  WHERE bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

union_metrics AS (
  SELECT * FROM l2_gas_fees_metrics
  UNION ALL
  SELECT * FROM l1_gas_fees_metrics
  UNION ALL
  SELECT * FROM upgrades_7702_metrics
  UNION ALL
  SELECT * FROM transaction_metrics
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM union_metrics