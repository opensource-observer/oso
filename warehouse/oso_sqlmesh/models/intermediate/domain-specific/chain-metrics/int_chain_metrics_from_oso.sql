MODEL (
  name oso.int_chain_metrics_from_oso,
  description "Chain-level metrics from OSO",
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
    no_gaps(
      time_column := sample_date,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
    "incrementalmusthaveforwardonly",
  )
);


WITH contract_metrics AS (
  SELECT
    deployment_date AS sample_date,
    contract_namespace AS chain,
    'CONTRACTS_DEPLOYED' AS metric_name,
    COUNT(DISTINCT contract_address) AS amount
  FROM oso.contracts_v0
  WHERE
    deployment_date BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

deployer_metrics AS (
  SELECT
    deployment_date AS sample_date,
    contract_namespace AS chain,
    'ACTIVE_DEPLOYERS' AS metric_name,
    COUNT(DISTINCT originating_address) AS amount
  FROM oso.contracts_v0
  WHERE
    deployment_date BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

userops_4337 AS (
  SELECT
    bucket_day AS sample_date,
    event_source AS chain,
    '4337_USEROPS' AS metric_name,
    SUM(count) AS amount
  FROM oso.int_events_daily__4337
  WHERE
    event_type = 'CONTRACT_INVOCATION_VIA_USEROP'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

active_accounts_4337 AS (
  SELECT
    bucket_day AS sample_date,
    event_source AS chain,
    '4337_ACTIVE_ACCOUNTS' AS metric_name,
    APPROX_DISTINCT(from_artifact_id) AS amount
  FROM oso.int_events_daily__4337
  WHERE
    event_type = 'CONTRACT_INVOCATION_VIA_USEROP'
    AND from_artifact_id IS NOT NULL
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

upgrades_7702 AS (
  SELECT
    DATE_TRUNC('DAY', block_timestamp::DATE) AS sample_date,
    chain,
    '7702_EOA_UPGRADES' AS metric_name,
    COUNT(DISTINCT from_address) AS amount
  FROM oso.stg_superchain__7702_transactions
  WHERE
    to_address = from_address
    AND block_timestamp BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

worldchain_userops AS (
  SELECT
    bucket_day AS sample_date,
    event_source AS chain,
    event_type AS metric_name,
    SUM(count) AS amount
  FROM oso.int_events_daily__worldchain_userops
  WHERE
    event_type = 'WORLDCHAIN_VERIFIED_USEROP'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

worldchain_users AS (
  SELECT
    bucket_day AS sample_date,
    event_source AS chain,
    'WORLDCHAIN_VERIFIED_USERS' AS metric_name,
    COUNT(DISTINCT from_artifact_id) AS amount
  FROM oso.int_events_daily__worldchain_userops
  WHERE
    event_type = 'WORLDCHAIN_VERIFIED_USEROP'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2, 3
),

union_metrics AS (
  SELECT * FROM contract_metrics
  UNION ALL
  SELECT * FROM deployer_metrics
  UNION ALL
  SELECT * FROM userops_4337
  UNION ALL
  SELECT * FROM active_accounts_4337
  UNION ALL
  SELECT * FROM upgrades_7702
  UNION ALL
  SELECT * FROM worldchain_userops
  UNION ALL
  SELECT * FROM worldchain_users
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM union_metrics