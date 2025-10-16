MODEL (
  name oso.int_optimism_grants_daily_defi_ltv_metrics_by_chain,
  description 'LTV metrics for DeFi chains (Superchain only)',
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
    SUM(CASE WHEN metric = 'tvl_90day' THEN amount ELSE 0 END)
      AS tvl_90day,
    SUM(CASE WHEN metric = 'tvs_90day' THEN amount ELSE 0 END)
      AS tvs_90day,
    SUM(CASE WHEN metric = 'fees_90day' THEN amount ELSE 0 END) * 90
      AS fees_90day,
    SUM(CASE WHEN metric = 'revenue_90day' THEN amount ELSE 0 END) * 90
      AS revenue_90day,
    SUM(CASE WHEN metric = 'userops_90day' THEN amount ELSE 0 END) * 90
      AS userops_90day
  FROM oso.int_optimism_grants_daily_defi_metrics_by_chain
  GROUP BY 1,2
),
metrics_alltime AS (
  SELECT
    m90.sample_date,
    m90.chain,
    (m90.sample_date - MIN(m.sample_date)) / 30 AS months_activity,
    MAX(CASE WHEN m.metric = 'tvl' THEN m.amount ELSE 0 END)
      AS tvl_alltime,
    MAX(CASE WHEN m.metric = 'tvs' THEN m.amount ELSE 0 END)
      AS tvs_alltime,
    SUM(CASE WHEN m.metric = 'fees' THEN m.amount ELSE 0 END)
      AS fees_alltime,
    SUM(CASE WHEN m.metric = 'revenue' THEN m.amount ELSE 0 END)
      AS revenue_alltime,
    SUM(CASE WHEN m.metric = 'userops' THEN m.amount ELSE 0 END)
      AS userops_alltime
  FROM metrics_90day AS m90
  JOIN oso.int_optimism_grants_daily_defi_metrics_by_chain AS m
    ON m90.sample_date <= m.sample_date
    AND m90.chain = m.chain
  GROUP BY 1,2
)

SELECT
  sample_date,
  chain,
  months_activity,
  tvl_90day,
  fees_90day,
  revenue_90day,
  userops_90day,
  tvs_90day,
  tvl_alltime,
  tvs_alltime,
  fees_alltime,
  revenue_alltime,
  userops_alltime
FROM metrics_alltime
JOIN metrics_90day USING (sample_date, chain)
ORDER BY 1,2,3