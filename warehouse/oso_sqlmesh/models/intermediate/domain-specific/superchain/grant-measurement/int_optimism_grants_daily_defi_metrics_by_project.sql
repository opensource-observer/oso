MODEL (
  name oso.int_optimism_grants_daily_defi_metrics_by_project,
  description 'Curated daily DeFi metrics for projects that received Optimism grants',
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
    metric_event_source AS chain,
    oso_project_name,
    CASE
      WHEN metric_model = 'layer2_gas_fees_amortized' THEN 'fees'
      WHEN metric_model = 'defillama_tvl' THEN 'tvl'
      WHEN metric_model = 'contract_invocations' THEN 'userops'
    END AS metric,
    SUM(CASE
      WHEN metric_model = 'layer2_gas_fees_amortized'
      THEN CAST(CAST(amount AS DECIMAL(38,0)) / DECIMAL '1000000000000000000' AS DECIMAL(38,18))
      ELSE CAST(amount AS DECIMAL(38,18))
    END) AS amount_dec
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
    amount_dec
  FROM base
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    'revenue' AS metric,
    CASE WHEN chain = 'OPTIMISM' THEN amount_dec ELSE amount_dec * DECIMAL '0.15' END AS amount_dec
  FROM base
  WHERE metric = 'fees'
),
rolling_windows AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric || '_7day' AS metric,
    SUM(amount_dec) OVER (
      PARTITION BY oso_project_name, chain, metric
      ORDER BY sample_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) / DECIMAL '7' AS amount_dec
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric || '_30day' AS metric,
    SUM(amount_dec) OVER (
      PARTITION BY oso_project_name, chain, metric
      ORDER BY sample_date
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) / DECIMAL '30' AS amount_dec
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric || '_90day' AS metric,
    SUM(amount_dec) OVER (
      PARTITION BY oso_project_name, chain, metric
      ORDER BY sample_date
      ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ) / DECIMAL '90' AS amount_dec
  FROM base_with_revenue
),
final AS (
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric,
    amount_dec
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    oso_project_name,
    metric,
    amount_dec
  FROM rolling_windows
)

SELECT
  sample_date::DATE AS sample_date,
  oso_project_name::VARCHAR AS oso_project_name,
  chain::VARCHAR AS chain,
  metric::VARCHAR AS metric,
  amount_dec::DOUBLE AS amount
FROM final