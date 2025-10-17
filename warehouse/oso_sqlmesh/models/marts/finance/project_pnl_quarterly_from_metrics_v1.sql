MODEL (
  name oso.project_pnl_quarterly_from_metrics_v1,
  description 'Quarterly P&L per project using metrics layer: income=funding_received, expense=funding_awarded.',
  dialect trino,
  kind FULL,
  partitioned_by year(quarter_start),
  tags ('model_stage=mart', 'entity_category=project'),
  audits (HAS_AT_LEAST_N_ROWS(threshold := 0))
);


WITH src AS (
  SELECT
      t.sample_date                                        AS sample_date,
      CAST(t.project_id AS VARCHAR)                        AS project_id,
      LOWER(COALESCE(p.project_name, 'unknown'))           AS project_name,
      LOWER(m.metric_name)                                      AS metric_name,
      TRY_CAST(t.amount AS DOUBLE)                         AS amount_usd
  FROM oso.timeseries_metrics_by_project_v0 t
  JOIN oso.metrics_v0 m
    ON m.metric_id = t.metric_id
  LEFT JOIN oso.projects_v1 p
    ON p.project_id = t.project_id
  WHERE LOWER(m.metric_name) IN ('funding_received', 'funding_awarded')
),

q AS (
  SELECT
      DATE_TRUNC('quarter', CAST(sample_date AS TIMESTAMP))                   AS quarter_start,
      YEAR(CAST(sample_date AS TIMESTAMP))                                    AS year,
      CONCAT('Q', CAST(QUARTER(CAST(sample_date AS TIMESTAMP)) AS VARCHAR))   AS quarter_label,
      project_id,
      project_name,
      SUM(CASE WHEN metric_name = 'funding_received' THEN amount_usd ELSE 0 END) AS income_usd,
      SUM(CASE WHEN metric_name = 'funding_awarded'  THEN amount_usd ELSE 0 END) AS expense_usd
  FROM src
  GROUP BY 1,2,3,4,5
)

SELECT
  quarter_start,
  year,
  quarter_label,
  project_id,
  project_name,
  income_usd,
  expense_usd,
  (COALESCE(income_usd,0) - COALESCE(expense_usd,0)) AS net_usd
FROM q
ORDER BY quarter_start, project_name;
