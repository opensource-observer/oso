MODEL(
  name oso.int_superchain_s8_onchain_metrics_by_project,
  description 'S8 onchain metrics by project with various aggregations and filters',
  kind full,
  dialect trino,
  partitioned_by (DAY("sample_date"), "metric_name", "chain"),
  grain(sample_date, chain, project_id, metric_name),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH metric_names AS (
  SELECT metric_name FROM (
    VALUES 
      ('contract_invocations'),
      ('layer2_gas_fees'),
      ('layer2_gas_fees_amortized'),
      ('defillama_tvl'),
      ('farcaster_users'),
      ('worldchain_users'),
      ('active_addresses_aggregation'),
      ('upgraded_eoa_users'),
      ('userops'),
      ('qualified_addresses')
      
  ) AS t(metric_name)
),

target_metrics AS (
  SELECT
    c.chain,
    mn.metric_name,
    CONCAT(c.chain, '_', mn.metric_name, '_monthly') AS full_metric_name
  FROM oso.int_superchain_chain_names AS c
  CROSS JOIN metric_names AS mn
),

metrics AS (
  SELECT
    m.metric_id,
    tm.chain,
    tm.metric_name
  FROM oso.metrics_v0 AS m
  JOIN target_metrics AS tm
    ON m.metric_name = tm.full_metric_name
),

projects AS (
  SELECT DISTINCT project_id
  FROM oso.projects_by_collection_v1
  WHERE collection_name LIKE '8-%'
)

SELECT DISTINCT
  tm.project_id,
  metrics.chain,
  tm.sample_date,
  metrics.metric_name,
  CASE
    WHEN metrics.metric_name LIKE '%_gas_fees%' THEN tm.amount / 1e18
    ELSE tm.amount END
  AS amount
FROM oso.timeseries_metrics_by_project_v0 AS tm
JOIN metrics
  ON tm.metric_id = metrics.metric_id
JOIN projects
  ON tm.project_id = projects.project_id