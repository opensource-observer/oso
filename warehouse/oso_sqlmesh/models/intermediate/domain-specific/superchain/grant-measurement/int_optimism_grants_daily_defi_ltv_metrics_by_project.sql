MODEL (
  name oso.int_optimism_grants_daily_defi_ltv_metrics_by_project,
  description 'LTV metrics for DeFi projects that received Optimism grants',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

WITH metrics_90day AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    SUM(CASE WHEN metric = 'tvl_90day' THEN amount ELSE 0 END)
      AS tvl_90day,
    SUM(CASE WHEN metric = 'fees_90day' THEN amount ELSE 0 END) * 90
      AS fees_90day,
    SUM(CASE WHEN metric = 'revenue_90day' THEN amount ELSE 0 END) * 90
      AS revenue_90day,
    SUM(CASE WHEN metric = 'userops_90day' THEN amount ELSE 0 END) * 90
      AS userops_90day
  FROM oso.int_optimism_grants_daily_defi_metrics_by_project
  GROUP BY 1,2,3
),
metrics_alltime AS (
  SELECT
    m90.sample_date,
    m90.chain,
    m90.oso_project_name,
    date_diff('day', MIN(m.sample_date), m90.sample_date) / 30.0 AS months_activity,
    MAX(CASE WHEN m.metric = 'tvl' THEN m.amount ELSE 0 END)
      AS tvl_alltime,
    SUM(CASE WHEN m.metric = 'fees' THEN m.amount ELSE 0 END)
      AS fees_alltime,
    SUM(CASE WHEN m.metric = 'revenue' THEN m.amount ELSE 0 END)
      AS revenue_alltime,
    SUM(CASE WHEN m.metric = 'userops' THEN m.amount ELSE 0 END)
      AS userops_alltime
  FROM metrics_90day AS m90
  JOIN oso.int_optimism_grants_daily_defi_metrics_by_project AS m
    ON m.sample_date <= m90.sample_date
    AND m90.chain = m.chain
    AND m90.oso_project_name = m.oso_project_name
  GROUP BY 1,2,3
)

SELECT
  sample_date,
  oso_project_name,
  chain,
  months_activity,
  tvl_90day,
  fees_90day,
  revenue_90day,
  userops_90day,
  tvl_alltime,
  fees_alltime,
  revenue_alltime,
  userops_alltime
FROM metrics_alltime
JOIN metrics_90day USING (sample_date, chain, oso_project_name)
ORDER BY 1,2,3