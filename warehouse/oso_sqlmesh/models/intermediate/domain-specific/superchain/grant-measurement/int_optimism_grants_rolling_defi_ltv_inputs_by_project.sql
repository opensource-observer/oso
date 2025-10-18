MODEL (
  name oso.int_optimism_grants_rolling_defi_ltv_inputs_by_project,
  description 'LTV inputs (TVL, fees, and userops) for DeFi projects that received Optimism grants',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  enabled true
);


WITH base AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric,
    SUM(amount) AS amount
  FROM oso.int_optimism_grants_rolling_defi_metrics_by_project
  GROUP BY 1,2,3,4
),
daily AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    SUM(CASE WHEN metric='tvl' THEN amount END) AS tvl,
    SUM(CASE WHEN metric='fees' THEN amount ELSE 0 END) AS fees,
    SUM(CASE WHEN metric='revenue' THEN amount ELSE 0 END) AS revenue,
    SUM(CASE WHEN metric='userops' THEN amount ELSE 0 END) AS userops
  FROM base
  GROUP BY 1,2,3
),
metrics_90day AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    SUM(CASE WHEN metric='tvl_90day' THEN amount ELSE 0 END) AS tvl_90day,
    SUM(CASE WHEN metric='fees_90day' THEN amount ELSE 0 END)*90.0 AS fees_90day,
    SUM(CASE WHEN metric='revenue_90day' THEN amount ELSE 0 END)*90.0 AS revenue_90day,
    SUM(CASE WHEN metric='userops_90day' THEN amount ELSE 0 END)*90.0 AS userops_90day
  FROM base
  GROUP BY 1,2,3
),
metrics_alltime AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    DATE_DIFF(
      'day',
      MIN(sample_date) OVER (PARTITION BY chain, oso_project_name),
      sample_date
    )/30.0 AS months_activity,
    MAX(tvl)
      OVER (PARTITION BY chain, oso_project_name ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS tvl_alltime,
    SUM(fees)
      OVER (PARTITION BY chain, oso_project_name ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS fees_alltime,
    SUM(revenue)
      OVER (PARTITION BY chain, oso_project_name ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS revenue_alltime,
    SUM(userops)
      OVER (PARTITION BY chain, oso_project_name ORDER BY sample_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS userops_alltime
  FROM daily
)

SELECT
  m.sample_date,
  m.oso_project_name,
  m.chain,
  m.months_activity,
  d.tvl_90day,
  d.fees_90day,
  d.revenue_90day,
  d.userops_90day,
  m.tvl_alltime,
  m.fees_alltime,
  m.revenue_alltime,
  m.userops_alltime
FROM metrics_alltime AS m
JOIN metrics_90day AS d
  ON m.sample_date = d.sample_date
  AND m.chain = d.chain
  AND m.oso_project_name = d.oso_project_name