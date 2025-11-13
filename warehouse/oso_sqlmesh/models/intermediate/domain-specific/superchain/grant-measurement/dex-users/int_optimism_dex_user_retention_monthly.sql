MODEL (
  name oso.int_optimism_dex_user_retention_monthly,
  description 'Monthly retention cohort analysis for DEX users on OP Mainnet with New/Retained/Dormant/Resurrected/Churned labels',
  dialect trino,
  kind full,
  grain (user_address, dex_project_name, activity_month),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH user_activity_monthly AS (
  SELECT
    user_address,
    dex_project_name,
    DATE_TRUNC('MONTH', bucket_day) AS activity_month,
    SUM(total_gas_fees) AS monthly_gas_fees,
    SUM(total_transactions) AS monthly_transactions,
    COUNT(DISTINCT bucket_day) AS days_active_in_month
  FROM oso.int_optimism_dex_user_events_daily
  GROUP BY 1, 2, 3
),
user_dex_first_month AS (
  SELECT
    user_address,
    dex_project_name,
    MIN(activity_month) AS first_month
  FROM user_activity_monthly
  GROUP BY 1, 2
),
-- Create a complete grid of all user+dex+month combinations
user_dex_combinations AS (
  SELECT DISTINCT
    a.user_address,
    a.dex_project_name,
    f.first_month
  FROM user_activity_monthly AS a
  LEFT JOIN user_dex_first_month AS f
    ON a.user_address = f.user_address
    AND a.dex_project_name = f.dex_project_name
),
all_months AS (
  SELECT DISTINCT activity_month
  FROM user_activity_monthly
),
user_dex_month_grid AS (
  SELECT
    u.user_address,
    u.dex_project_name,
    u.first_month,
    m.activity_month
  FROM user_dex_combinations AS u
  CROSS JOIN all_months AS m
  WHERE m.activity_month >= u.first_month
),
-- Join actual activity with the grid
user_month_status AS (
  SELECT
    g.user_address,
    g.dex_project_name,
    g.activity_month,
    g.first_month,
    COALESCE(a.monthly_gas_fees, 0) AS monthly_gas_fees,
    COALESCE(a.monthly_transactions, 0) AS monthly_transactions,
    COALESCE(a.days_active_in_month, 0) AS days_active_in_month,
    CASE WHEN a.activity_month IS NOT NULL THEN 1 ELSE 0 END AS is_active
  FROM user_dex_month_grid AS g
  LEFT JOIN user_activity_monthly AS a
    ON g.user_address = a.user_address
    AND g.dex_project_name = a.dex_project_name
    AND g.activity_month = a.activity_month
),
-- Calculate previous activity patterns
activity_windows AS (
  SELECT
    user_address,
    dex_project_name,
    activity_month,
    first_month,
    is_active,
    monthly_gas_fees,
    monthly_transactions,
    days_active_in_month,
    -- Get last active month before current month
    MAX(CASE WHEN is_active = 1 THEN activity_month END) 
      OVER (
        PARTITION BY user_address, dex_project_name 
        ORDER BY activity_month 
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
      ) AS last_active_month
  FROM user_month_status
),
-- Classify retention status
classified AS (
  SELECT
    user_address,
    dex_project_name,
    activity_month,
    first_month,
    is_active,
    monthly_gas_fees,
    monthly_transactions,
    days_active_in_month,
    last_active_month,
    -- Calculate months since last activity
    CASE 
      WHEN last_active_month IS NULL THEN NULL
      ELSE DATE_DIFF('month', last_active_month, activity_month)
    END AS months_since_last_active,
    -- Classify user status
    CASE
      -- Active users
      WHEN is_active = 1 AND activity_month = first_month THEN 'new'
      WHEN is_active = 1 AND last_active_month IS NOT NULL 
        AND DATE_DIFF('month', last_active_month, activity_month) >= 3 THEN 'resurrected'
      WHEN is_active = 1 THEN 'retained'
      -- Inactive users
      WHEN is_active = 0 AND last_active_month IS NOT NULL
        AND DATE_DIFF('month', last_active_month, activity_month) BETWEEN 1 AND 2 THEN 'dormant'
      WHEN is_active = 0 AND last_active_month IS NOT NULL
        AND DATE_DIFF('month', last_active_month, activity_month) >= 3 THEN 'churned'
      ELSE 'unknown'
    END AS retention_status,
    -- Calculate cohort metrics
    DATE_DIFF('month', first_month, activity_month) AS months_since_first_activity
  FROM activity_windows
)

SELECT
  user_address,
  dex_project_name,
  activity_month,
  first_month AS cohort_month,
  retention_status,
  months_since_first_activity AS cohort_age_months,
  months_since_last_active,
  is_active,
  days_active_in_month,
  monthly_transactions,
  monthly_gas_fees,
  -- Add cohort period labels for easier analysis
  CASE
    WHEN months_since_first_activity = 0 THEN 'M0'
    WHEN months_since_first_activity = 1 THEN 'M1'
    WHEN months_since_first_activity = 2 THEN 'M2'
    WHEN months_since_first_activity = 3 THEN 'M3'
    WHEN months_since_first_activity <= 6 THEN 'M4-M6'
    WHEN months_since_first_activity <= 12 THEN 'M7-M12'
    ELSE 'M12+'
  END AS cohort_period_label
FROM classified
WHERE retention_status != 'unknown'
ORDER BY
  dex_project_name,
  user_address,
  activity_month