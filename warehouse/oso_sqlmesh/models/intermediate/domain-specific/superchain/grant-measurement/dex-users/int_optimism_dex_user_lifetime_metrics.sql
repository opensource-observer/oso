MODEL (
  name oso.int_optimism_dex_user_lifetime_metrics,
  description 'Lifetime metrics for each user per DEX on OP Mainnet',
  dialect trino,
  kind full,
  grain (user_address, dex_project_name),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  user_address,
  dex_project_name,
  MIN(bucket_day) AS first_day_with_dex,
  MAX(bucket_day) AS last_day_with_dex,
  COUNT(DISTINCT bucket_day) AS days_active_with_dex,
  SUM(total_transactions) AS total_transactions_on_dex,
  SUM(total_gas_fees) AS total_gas_fees_on_dex,
  DATE_DIFF('day', MIN(bucket_day), MAX(bucket_day)) + 1 AS dex_tenure_days,
  CAST(COUNT(DISTINCT bucket_day) AS DOUBLE) / NULLIF(DATE_DIFF('day', MIN(bucket_day), MAX(bucket_day)) + 1, 0) AS dex_activity_ratio
FROM oso.int_optimism_dex_user_events_daily
GROUP BY 1, 2
ORDER BY 
  total_gas_fees_on_dex DESC,
  user_address,
  dex_project_name

