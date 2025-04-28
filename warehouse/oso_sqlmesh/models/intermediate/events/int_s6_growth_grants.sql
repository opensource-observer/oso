MODEL (
  name oso.int_s6_growth_grants,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column transaction_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by (DAY(transaction_day), project_name),
  grain (transaction_day, project_name),
  tags (
    'entity_category=project'
  ),
  audits (
    not_null(columns := (project_name, transaction_day))
  )
);

WITH allowed_projects AS (
    SELECT project_name
    FROM (VALUES
        ('renzo-protocol'),
        ('ether-fi')
    ) AS t(project_name)
)

SELECT
    p.project_name,
    DATE_TRUNC('DAY', tm.sample_date) AS transaction_day,
    SUM(CASE WHEN m.metric_name LIKE '%transactions_daily' THEN tm.amount ELSE 0 END) AS transactions,
    SUM(CASE WHEN m.metric_name LIKE '%active_addresses_daily' THEN tm.amount ELSE 0 END) AS active_addresses,
    SUM(CASE WHEN m.metric_name LIKE '%gas_fees_daily' THEN tm.amount ELSE 0 END) AS gas_fees
FROM oso.projects_v1 p 
JOIN oso.int_artifacts_by_project_all_sources a ON p.project_id = a.project_id
JOIN oso.timeseries_metrics_by_artifact_v0 tm ON a.artifact_id = tm.artifact_id
JOIN oso.metrics_v0 m ON m.metric_id = tm.metric_id
WHERE tm.sample_date >= '2024-01-01'
    AND p.project_name IN (SELECT project_name FROM allowed_projects)
GROUP BY
    p.project_name,
    DATE_TRUNC('DAY', tm.sample_date)
