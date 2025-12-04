MODEL (
  name oso.int_optimism_grants_metrics_by_project,
  description 'Timeseries metrics by project for Optimism grants',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
);

WITH projects AS (
  SELECT DISTINCT
    oso_project_id,
    oso_project_name,
    oso_project_display_name
  FROM oso.int_optimism_grants
  WHERE oso_project_id IS NOT NULL
),

metrics AS (
  SELECT
    p.oso_project_id,
    p.oso_project_name,
    p.oso_project_display_name,
    tm.sample_date,
    m.metric_name,
    m.metric_model,
    m.display_name AS metric_display_name,
    m.metric_event_source,
    m.metric_time_aggregation,
    tm.amount
  FROM oso.timeseries_metrics_by_project_v0 AS tm
  JOIN projects AS p
    ON tm.project_id = p.oso_project_id
  JOIN oso.metrics_v0 AS m
    ON tm.metric_id = m.metric_id
  WHERE
    m.metric_model NOT IN ('funding_awarded', 'funding_received')
    AND tm.sample_date >= DATE('2022-01-01')
    AND m.metric_time_aggregation IN ('daily', 'monthly')
),

enriched_metrics AS (
  SELECT
    metrics.*,
    CASE
      WHEN metrics.metric_event_source = 'GITHUB' THEN 'GITHUB'
      WHEN chains.is_superchain = TRUE THEN 'SUPERCHAIN'
      WHEN chains.is_layer2 = TRUE THEN 'LAYER2'
      WHEN chains.chain = 'MAINNET' THEN 'ETHEREUM'
      WHEN chains.has_tvl = TRUE THEN 'LAYER1'
      ELSE 'OTHER'
    END AS metric_event_source_category
  FROM metrics
  LEFT JOIN oso.int_chains AS chains
    ON metrics.metric_event_source = chains.chain
)
SELECT
  oso_project_id,
  oso_project_name,
  oso_project_display_name,
  sample_date,
  metric_name,
  metric_model,
  metric_display_name,
  metric_event_source,
  metric_event_source_category,
  metric_time_aggregation,
  amount
FROM enriched_metrics