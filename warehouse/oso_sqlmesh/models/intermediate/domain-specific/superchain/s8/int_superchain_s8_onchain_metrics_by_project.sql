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


WITH metrics AS (
  SELECT
    m.metric_id,
    c.chain,
    REPLACE(m.metric_name, c.chain || '_', '') AS metric_name
  FROM oso.metrics_v0 AS m
  JOIN oso.int_superchain_chain_names AS c
    ON m.metric_name LIKE CONCAT(c.chain, '_%_monthly')      
  WHERE
    -- TODO: replace these with the correct metric names
    m.metric_name LIKE '%_contract_invocations_monthly'
    OR m.metric_name LIKE '%_gas_fees_monthly'
    OR m.metric_name LIKE '%_defillama_tvl_monthly'
    OR m.metric_name LIKE '%_userops_monthly'
    OR m.metric_name LIKE '%_farcaster_users_monthly'
    OR m.metric_name LIKE '%_worldchain_verified_users_monthly'
    OR m.metric_name LIKE '%_upgraded_eoa_users_monthly'
    OR m.metric_name LIKE '%_qualified_addresses_monthly'
    OR m.metric_name LIKE '%_active_addresses_aggregation_monthly'
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
  tm.amount
FROM oso.timeseries_metrics_by_project_v0 AS tm
JOIN metrics
  ON tm.metric_id = metrics.metric_id
JOIN projects
  ON tm.project_id = projects.project_id