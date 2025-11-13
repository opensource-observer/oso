MODEL (
  name oso.int_optimism_dex_users,
  description 'DEX user metrics per DEX and overall on OP Mainnet',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

WITH user_activity_by_dex AS (
  SELECT
    user_address,
    dex_project_name,
    MIN(bucket_day) AS first_day_of_activity,
    MAX(bucket_day) AS last_day_of_activity,
    SUM(total_gas_fees) AS total_gas_fees,
    SUM(total_transactions) AS total_transactions,
    COUNT(DISTINCT bucket_day) AS days_active
  FROM oso.int_optimism_dex_user_events_daily
  GROUP BY 1,2
),
user_activity_overall AS (
  SELECT
    user_address,
    MIN(bucket_day) AS first_day_of_activity_overall,
    MAX(bucket_day) AS last_day_of_activity_overall,
    SUM(total_gas_fees) AS total_gas_fees_overall,
    SUM(total_transactions) AS total_transactions_overall,
    COUNT(DISTINCT bucket_day) AS days_active_overall,
    COUNT(DISTINCT dex_project_name) AS unique_dexs_used
  FROM oso.int_optimism_dex_user_events_daily
  GROUP BY 1
)

SELECT
  dex.user_address,
  dex.dex_project_name,
  -- Per-DEX metrics
  dex.first_day_of_activity AS first_day_with_dex,
  dex.last_day_of_activity AS last_day_with_dex,
  dex.days_active AS days_active_with_dex,
  dex.total_transactions AS total_transactions_on_dex,
  dex.total_gas_fees AS total_gas_fees_on_dex,
  -- Overall Optimism metrics
  overall.first_day_of_activity_overall,
  overall.last_day_of_activity_overall,
  overall.days_active_overall,
  overall.unique_dexs_used,
  overall.total_transactions_overall,
  overall.total_gas_fees_overall,
  -- Calculated metrics
  DATE_DIFF('day', dex.first_day_of_activity, dex.last_day_of_activity) + 1 AS dex_tenure_days,
  DATE_DIFF('day', overall.first_day_of_activity_overall, overall.last_day_of_activity_overall) + 1 AS overall_tenure_days,
  CASE 
    WHEN overall.first_day_of_activity_overall = dex.first_day_of_activity 
    THEN true 
    ELSE false 
  END AS is_first_dex,
  CAST(dex.total_transactions AS DOUBLE) / overall.total_transactions_overall AS pct_transactions_on_dex,
  CAST(dex.total_gas_fees AS DOUBLE) / overall.total_gas_fees_overall AS pct_gas_fees_on_dex
FROM user_activity_by_dex AS dex
LEFT JOIN user_activity_overall AS overall
  ON dex.user_address = overall.user_address
ORDER BY 
  overall.total_gas_fees_overall DESC,
  dex.user_address,
  dex.total_gas_fees DESC