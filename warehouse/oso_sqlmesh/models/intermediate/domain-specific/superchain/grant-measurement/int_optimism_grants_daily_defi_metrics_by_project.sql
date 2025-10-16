MODEL (
  name oso.int_optimism_grants_daily_defi_metrics_by_project,
  description 'Curated daily DeFi metrics for projects that received Optimism grants',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

WITH base AS (
  SELECT
    sample_date,
    metric_event_source AS chain,
    oso_project_name,
    CASE
      WHEN metric_model = 'layer2_gas_fees_amortized' THEN 'fees'
      WHEN metric_model = 'defillama_tvl' THEN 'tvl'
      WHEN metric_model = 'contract_invocations' THEN 'userops'
    END as metric,
    SUM(CASE
      WHEN metric_model = 'layer2_gas_fees_amortized' THEN amount/1e18
      ELSE amount
    END) AS amount
  FROM oso.int_optimism_grants_metrics_by_project
  WHERE 
    metric_event_source_category = 'SUPERCHAIN'
    AND metric_model IN (
      'defillama_tvl',
      'layer2_gas_fees_amortized',
      'contract_invocations'
    )
    AND metric_event_source NOT IN ('CELO')
    AND metric_time_aggregation = 'daily'
  GROUP BY 1,2,3,4
),
base_with_revenue AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric,
    amount
  FROM base
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    'revenue' AS metric,
    CASE WHEN chain = 'OPTIMISM' THEN amount ELSE amount * 0.15 END AS amount
  FROM base
  WHERE metric = 'fees'
),
rolling_windows AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric || '_7day' AS metric,
    SUM(amount) OVER (PARTITION BY oso_project_name, chain, metric ORDER BY sample_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) / 7 AS amount
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric || '_30day' AS metric,
    SUM(amount) OVER (PARTITION BY oso_project_name, chain, metric ORDER BY sample_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) / 30 AS amount
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric || '_90day' AS metric,
    SUM(amount) OVER (PARTITION BY oso_project_name, chain, metric ORDER BY sample_date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) / 90 AS amount
  FROM base_with_revenue
),
final AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric,
    amount
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric,
    amount
  FROM rolling_windows
)
SELECT
  sample_date,
  oso_project_name,
  chain,
  metric,
  amount
FROM final
ORDER BY 1,2,3,4