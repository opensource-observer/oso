MODEL (
  name oso.int_optimism_grants_daily_defi_ltv_metrics_by_chain,
  description 'LTV metrics for DeFi chains (Superchain only)',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

WITH base AS (
  SELECT
    sample_date,
    chain,
    metric,
    SUM(amount) AS amount
  FROM oso.int_optimism_grants_daily_defi_metrics_by_chain
  GROUP BY 1,2,3
),
metrics_90day AS (
  SELECT
    sample_date,
    chain,
    SUM(CASE WHEN metric='tvl_90day' THEN amount ELSE 0 END) AS tvl_90day,
    SUM(CASE WHEN metric='tvs_90day' THEN amount ELSE 0 END) AS tvs_90day,
    SUM(CASE WHEN metric='fees_90day' THEN amount ELSE 0 END)*90.0 AS fees_90day,
    SUM(CASE WHEN metric='revenue_90day' THEN amount ELSE 0 END)*90.0 AS revenue_90day,
    SUM(CASE WHEN metric='userops_90day' THEN amount ELSE 0 END)*90.0 AS userops_90day
  FROM base
  GROUP BY 1,2
),
metrics_alltime AS (
  SELECT
    sample_date,
    chain,
    -- months since first activity for this chain
    DATE_DIFF(
      'day',
      MIN(sample_date) OVER (PARTITION BY chain),
      sample_date
    )/30.0 AS months_activity,

    -- peak-to-date levels
    MAX(CASE WHEN metric='tvl' THEN amount END)
      OVER (PARTITION BY chain ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS tvl_alltime,
    MAX(CASE WHEN metric='tvs' THEN amount END)
      OVER (PARTITION BY chain ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS tvs_alltime,

    -- cumulative-to-date flows
    SUM(CASE WHEN metric='fees' THEN amount END)
      OVER (PARTITION BY chain ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS fees_alltime,
    SUM(CASE WHEN metric='revenue' THEN amount END)
      OVER (PARTITION BY chain ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS revenue_alltime,
    SUM(CASE WHEN metric='userops' THEN amount END)
      OVER (PARTITION BY chain ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS userops_alltime
  FROM oso.int_optimism_grants_daily_defi_metrics_by_chain
)

SELECT
  m.sample_date,
  m.chain,
  m.months_activity,
  d.tvl_90day,
  d.fees_90day,
  d.revenue_90day,
  d.userops_90day,
  d.tvs_90day,
  m.tvl_alltime,
  m.tvs_alltime,
  m.fees_alltime,
  m.revenue_alltime,
  m.userops_alltime
FROM metrics_alltime AS m
JOIN metrics_90day AS d
  ON m.sample_date = d.sample_date
  AND m.chain = d.chain
ORDER BY 1,2