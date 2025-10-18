MODEL (
  name oso.int_optimism_grants_rolling_defi_metrics_by_chain,
  description 'Rolling DeFi metrics by chain (Superchain only)',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  enabled true
);

WITH base AS (
  SELECT
    cm.sample_date,
    cm.chain,
    CASE
      WHEN cm.metric_name = 'LAYER2_GAS_FEES' THEN 'fees'
      WHEN cm.metric_name = 'DEFILLAMA_TVL' THEN 'tvl'
      WHEN cm.metric_name = 'L2BEAT_ACTIVITY_UOPS_COUNT' THEN 'userops'
      WHEN cm.metric_name = 'L2BEAT_TVS_EXTERNAL' THEN 'tvs'
      WHEN cm.metric_name = 'L2BEAT_TVS_NATIVE' THEN 'tvs'
      WHEN cm.metric_name = 'L2BEAT_TVS_CANONICAL' THEN 'tvs'
    END as metric,
    cm.amount::DOUBLE AS amount
  FROM oso.int_chain_metrics AS cm
  JOIN oso.int_chains AS c
    ON cm.chain = c.chain
  WHERE 
    c.is_superchain = TRUE
    AND cm.metric_name IN ('LAYER2_GAS_FEES', 'DEFILLAMA_TVL', 'L2BEAT_ACTIVITY_UOPS_COUNT', 'L2BEAT_TVS_EXTERNAL', 'L2BEAT_TVS_NATIVE', 'L2BEAT_TVS_CANONICAL')
),
grouped_metrics AS (
  SELECT
    sample_date,
    chain,
    metric,
    SUM(amount) AS amount
  FROM base
  GROUP BY 1,2,3
),
base_with_revenue AS (
  SELECT
    sample_date,
    chain,
    metric,
    amount
  FROM grouped_metrics
  UNION ALL
  SELECT
    sample_date,
    chain,
    'revenue' AS metric,
    CASE
      WHEN chain = 'OPTIMISM' THEN amount
      ELSE amount * 0.15
    END AS amount
  FROM grouped_metrics
  WHERE metric = 'fees'
),
rolling_windows AS (
  SELECT
    sample_date,
    chain,
    metric || '_7day' AS metric,
    SUM(amount) OVER (PARTITION BY chain, metric ORDER BY sample_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) / 7.0 AS amount
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    metric || '_30day' AS metric,
    SUM(amount) OVER (PARTITION BY chain, metric ORDER BY sample_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) / 30.0 AS amount
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    metric || '_90day' AS metric,
    SUM(amount) OVER (PARTITION BY chain, metric ORDER BY sample_date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) / 90.0 AS amount
  FROM base_with_revenue
),
final AS (
  SELECT
    sample_date,
    chain,
    metric,
    amount
  FROM base_with_revenue
  UNION ALL
  SELECT
    sample_date,
    chain,
    metric,
    amount
  FROM rolling_windows
)
SELECT
  sample_date::DATE AS sample_date,
  chain::VARCHAR AS chain,
  metric::VARCHAR AS metric,
  amount::DOUBLE AS amount
FROM final
