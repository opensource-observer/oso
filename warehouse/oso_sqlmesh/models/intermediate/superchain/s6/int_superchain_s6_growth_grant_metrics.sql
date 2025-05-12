MODEL (
  name oso.int_superchain_s6_growth_grant_metrics,
  description "Aggregates transactions, contract invocations, and active addresses for S6 growth grants",
  kind full,
  dialect trino,
  grain (project_id, sample_date),
  tags (
    'entity_category=project'
  ),
  audits (
    not_null(columns := (project_id, sample_date))
  )
);

WITH allowed_projects AS (
    SELECT DISTINCT project_id
    FROM oso.projects_by_collection_v1
    WHERE collection_name = 'op-s6-growth-grants'
),

daily_metrics AS (
  SELECT m.metric_id
  FROM oso.metrics_v0 AS m
  JOIN oso.int_superchain_chain_names AS c
    ON m.metric_name LIKE CONCAT(c.chain, '_%_daily')
)

SELECT
  tm.project_id,
  tm.sample_date,
  SUM(
    CASE WHEN m.metric_name LIKE '%transactions%' THEN tm.amount
    ELSE 0
    END
  ) AS transactions,
  SUM(
    CASE WHEN m.metric_name LIKE '%contract_invocations%' THEN tm.amount
    ELSE 0
    END
  ) AS contract_invocations,
  SUM(
    CASE WHEN m.metric_name LIKE '%active_addresses%' THEN tm.amount
    ELSE 0
    END
  ) AS active_addresses,
  SUM(
    CASE WHEN m.metric_name LIKE '%gas_fees%' THEN tm.amount
    ELSE 0
    END
  ) AS gas_fees,
  SUM(
    CASE WHEN m.metric_name LIKE '%defillama_tvl%' THEN tm.amount
    ELSE 0
    END
  ) AS defillama_tvl
FROM oso.timeseries_metrics_by_project_v0 AS tm
JOIN oso.metrics_v0 m ON m.metric_id = tm.metric_id
WHERE
  tm.sample_date >= DATE '2024-01-01'
  AND tm.project_id IN (SELECT project_id FROM allowed_projects)
  AND m.metric_id IN (SELECT metric_id FROM daily_metrics)
GROUP BY
  tm.project_id,
  tm.sample_date