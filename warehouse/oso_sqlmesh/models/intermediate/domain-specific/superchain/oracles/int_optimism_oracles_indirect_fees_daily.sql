MODEL (
  name oso.int_optimism_oracles_indirect_fees_daily,
  description "Optimism oracles indirect fees daily",
  dialect trino,
  kind incremental_by_time_range(
    time_column bucket_day,
    batch_size 120,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true,
    on_destructive_change warn,
    auto_restatement_cron @default_auto_restatement_cron
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
  tags (
    "entity_category=project",
  )
);

WITH events AS (
  SELECT
    DATE_TRUNC('DAY', block_timestamp) AS bucket_day,
    project_name AS oracle_name,
    to_address_tx AS to_address,
    gas_used_tx::DOUBLE / 1e18 * gas_price_tx::DOUBLE AS l2_tx_fees,
    transaction_hash
  FROM oso.int_optimism_static_calls_to_oracles
  WHERE
    block_timestamp BETWEEN @start_dt AND @end_dt
    AND project_name IS NOT NULL
),
oracles_per_txn AS (
  SELECT
    transaction_hash,
    COUNT(DISTINCT oracle_name)::DOUBLE AS num_oracles,
    COUNT(*) AS num_traces_per_txn
  FROM events
  GROUP BY 1
),
amortized_events AS (
  SELECT
    bucket_day,
    oracle_name,
    to_address,
    SUM(l2_tx_fees / num_traces_per_txn / num_oracles) AS l2_tx_fees,
    SUM(1.0 / num_oracles)::DOUBLE AS tx_count
  FROM events
  JOIN oracles_per_txn
    ON events.transaction_hash = oracles_per_txn.transaction_hash
  GROUP BY 1, 2, 3
),
apps AS (
  SELECT DISTINCT
    artifact_name,
    project_name AS to_project_name
  FROM oso.artifacts_by_project_v1
  WHERE
    project_source = 'OSS_DIRECTORY'
    AND project_namespace = 'oso'
    AND artifact_source = 'OPTIMISM'
)

SELECT
  ae.bucket_day,
  ae.oracle_name,
  ae.to_address,
  apps.to_project_name,
  ae.l2_tx_fees,
  ae.tx_count::DOUBLE AS tx_count
FROM amortized_events AS ae
LEFT JOIN apps
  ON ae.to_address = apps.artifact_name
ORDER BY 1