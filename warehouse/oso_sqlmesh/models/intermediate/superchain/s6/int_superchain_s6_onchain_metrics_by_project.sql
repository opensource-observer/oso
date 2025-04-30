MODEL (
  name oso.int_superchain_s6_onchain_metrics_by_project,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by (DAY(sample_date), project_id),
  grain (sample_date, project_id),
  tags (
    'entity_category=project'
  ),
  audits (
    not_null(columns := (project_id, sample_date))
  )
);

WITH allowed_collections AS (
    SELECT collection_name
    FROM (VALUES
      ('op-rpgf3'),
      ('8-1'),
      ('velodrome-users'),
      ('7-2'),
      ('ethereum-crypto-ecosystems'),
      ('arb-stylus'),
      ('op-growthgrants-s6'),
      ('op-rpgf2'),
      ('op-retrofunding-5'),
      ('polygon-crypto-ecosystems'),
      ('op-govgrants'),
      ('arb-onchain'),
      ('solana-crypto-ecosystems'),
      ('arbitrum-crypto-ecosystems'),
      ('8-2'),
      ('scroll-crypto-ecosystems'),
      ('thank-arb-grantees'),
      ('7-1'),
      ('zksync-crypto-ecosystems'),
      ('gg-20'),
      ('arb-stip-1'),
      ('op-onchain'),
      ('optimism'),
      ('op-retrofunding-4'),
      ('celo-crypto-ecosystems'),
      ('gg22-apps-dapps-apps'),
      ('base-crypto-ecosystems')
    ) AS t(collection_name)
), allowed_projects AS (
  SELECT DISTINCT
    p.project_id
    FROM oso.projects_by_collection_v1 AS p
    WHERE p.collection_name IN (SELECT collection_name FROM allowed_collections)
)

SELECT
  p.project_id,
  tm.sample_date,
  SUM(CASE WHEN m.metric_name LIKE '%transactions_daily' THEN tm.amount ELSE 0 END) AS transactions,
  SUM(CASE WHEN m.metric_name LIKE '%active_addresses_daily' THEN tm.amount ELSE 0 END) AS active_addresses,
  SUM(CASE WHEN m.metric_name LIKE '%gas_fees_daily' THEN tm.amount ELSE 0 END) AS gas_fees
FROM oso.projects_v1 p 
JOIN oso.timeseries_metrics_by_project_v0 tm ON p.project_id = tm.project_id
JOIN oso.metrics_v0 m ON m.metric_id = tm.metric_id
WHERE tm.sample_date >= DATE '2024-01-01'
  AND p.project_id IN (SELECT project_id FROM allowed_projects)
GROUP BY
  p.project_id,
  tm.sample_date
