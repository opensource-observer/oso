MODEL (
  name oso.int_optimism_user_profiles,
  description 'User profiles for DEX users including both DEX-specific and overall OP Mainnet activity metrics',
  dialect trino,
  kind full,
  grain (user_address),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH dex_users AS (
  SELECT DISTINCT user_address
  FROM oso.int_optimism_dex_user_events_daily
),
user_chain_activity AS (
  SELECT
    e.user_address,
    MIN(e.bucket_day) AS first_day_of_activity_on_op_mainnet,
    MAX(e.bucket_day) AS last_day_of_activity_on_op_mainnet,
    SUM(e.total_transactions) AS total_transactions_on_op_mainnet,
    SUM(e.total_gas_fees) AS total_gas_fees_on_op_mainnet,
    COUNT(DISTINCT e.bucket_day) AS total_days_active_on_op_mainnet,
    DATE_DIFF('day', MIN(e.bucket_day), MAX(e.bucket_day)) + 1 AS total_tenure_days_on_op_mainnet
  FROM oso.int_optimism_user_events_daily AS e
  INNER JOIN dex_users AS d ON e.user_address = d.user_address
  GROUP BY 1
),
user_dex_activity AS (
  SELECT
    user_address,
    MIN(bucket_day) AS first_day_of_dex_activity,
    MAX(bucket_day) AS last_day_of_dex_activity,
    COUNT(DISTINCT bucket_day) AS total_days_active_on_dexs,
    COUNT(DISTINCT dex_project_name) AS unique_dexs_used,
    SUM(total_transactions) AS total_transactions_on_dexs,
    SUM(total_gas_fees) AS total_gas_fees_on_dexs,
    DATE_DIFF('day', MIN(bucket_day), MAX(bucket_day)) + 1 AS total_tenure_days_on_dexs,
    CAST(COUNT(DISTINCT bucket_day) AS DOUBLE) / NULLIF(DATE_DIFF('day', MIN(bucket_day), MAX(bucket_day)) + 1, 0) AS total_activity_ratio_on_dexs
  FROM oso.int_optimism_dex_user_events_daily
  GROUP BY 1
)

SELECT
  d.user_address,
  -- DEX activity metrics
  d.first_day_of_dex_activity,
  d.last_day_of_dex_activity,
  d.total_days_active_on_dexs,
  d.unique_dexs_used,
  d.total_transactions_on_dexs,
  d.total_gas_fees_on_dexs,
  d.total_tenure_days_on_dexs,
  d.total_activity_ratio_on_dexs,
  -- Overall OP Mainnet activity
  c.first_day_of_activity_on_op_mainnet,
  c.last_day_of_activity_on_op_mainnet,
  c.total_transactions_on_op_mainnet,
  c.total_gas_fees_on_op_mainnet,
  c.total_days_active_on_op_mainnet,
  c.total_tenure_days_on_op_mainnet,
  -- Calculated ratios (how much of their activity is DEX?)
  CAST(d.total_gas_fees_on_dexs AS DOUBLE) / NULLIF(c.total_gas_fees_on_op_mainnet, 0) AS pct_gas_fees_on_dexs,
  CAST(d.total_transactions_on_dexs AS DOUBLE) / NULLIF(c.total_transactions_on_op_mainnet, 0) AS pct_transactions_on_dexs,
  CAST(d.total_days_active_on_dexs AS DOUBLE) / NULLIF(c.total_days_active_on_op_mainnet, 0) AS pct_days_active_on_dexs
FROM user_dex_activity AS d
JOIN user_chain_activity AS c
  ON d.user_address = c.user_address
ORDER BY c.total_gas_fees_on_op_mainnet DESC
