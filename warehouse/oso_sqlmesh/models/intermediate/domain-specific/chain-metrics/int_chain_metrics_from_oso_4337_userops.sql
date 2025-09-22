MODEL (
  name oso.int_chain_metrics_from_oso_4337_userops,
  description "Chain-level metrics from OSO 4337 userops",
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
  partitioned_by YEAR("sample_date"),
  grain (sample_date, chain, metric_name),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
    "incrementalmustdefinenogapsaudit",
  )
);

WITH userops_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    '4337_USEROPS' AS metric_name,
    SUM(count) AS amount
  FROM oso.int_events_daily__4337
  WHERE
    event_type = 'CONTRACT_INVOCATION_VIA_USEROP'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

active_accounts_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    '4337_ACTIVE_ACCOUNTS' AS metric_name,
    APPROX_DISTINCT(from_artifact_id) AS amount
  FROM oso.int_events_daily__4337
  WHERE
    event_type = 'CONTRACT_INVOCATION_VIA_USEROP'
    AND from_artifact_id IS NOT NULL
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

worldchain_userops_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    'WORLDCHAIN_VERIFIED_USEROPS' AS metric_name,
    SUM(count) AS amount
  FROM oso.int_events_daily__worldchain_userops
  WHERE
    event_type = 'WORLDCHAIN_VERIFIED_USEROP'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

worldchain_users_metrics AS (
  SELECT
    DATE_TRUNC('DAY', bucket_day::DATE) AS sample_date,
    event_source AS chain,
    'WORLDCHAIN_VERIFIED_USERS' AS metric_name,
    APPROX_DISTINCT(from_artifact_id) AS amount
  FROM oso.int_events_daily__worldchain_userops
  WHERE
    event_type = 'WORLDCHAIN_VERIFIED_USEROP'
    AND bucket_day BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

union_metrics AS (
  SELECT * FROM userops_metrics
  UNION ALL
  SELECT * FROM active_accounts_metrics
  UNION ALL
  SELECT * FROM worldchain_userops_metrics
  UNION ALL
  SELECT * FROM worldchain_users_metrics
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM union_metrics