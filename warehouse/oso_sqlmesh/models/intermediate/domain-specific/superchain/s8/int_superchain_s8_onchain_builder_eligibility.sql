MODEL (
  name oso.int_superchain_s8_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S8 onchain builder round",
  dialect trino,
  kind full,
  grain (sample_date, project_id),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

@DEF(transactions_threshold, 1000);
@DEF(days_with_onchain_activity_threshold, 10);

WITH
  -- Define measurement dates (e.g., end of each month)
  measurement_dates AS (
    SELECT
      measurement_date,
      date_trunc('month', measurement_date) AS sample_date
    FROM (
      SELECT measurement_date
      FROM (VALUES 
        (DATE('2025-08-31')),
        (DATE('2025-09-30')),
        (DATE('2025-10-31')),
        (DATE('2025-11-30')),
        (DATE('2025-12-31')),
        (DATE('2026-01-31'))
      ) AS t(measurement_date)
    )
  ),

  -- Get the daily metric IDs for the Superchain
  daily_metrics AS (
    SELECT
      m.metric_id,
      REPLACE(m.metric_name, '_daily', '') AS metric_group
    FROM oso.metrics_v0 AS m
    JOIN oso.int_superchain_chain_names AS c
      ON m.metric_name LIKE CONCAT(c.chain, '_%_daily')
      -- TODO: replace this with "internal_transactions_daily"
    WHERE m.metric_name LIKE '%_contract_invocations_daily'
  ),

  -- For each measurement date, get all projects
  project_measurement_dates AS (
    SELECT DISTINCT
      p.project_id,
      md.measurement_date,
      md.sample_date
    FROM oso.projects_v1 AS p
    CROSS JOIN measurement_dates AS md
  ),

  -- Calculate metrics for each project and measurement date
  -- by looking back 180 days from each measurement date
  project_metrics AS (
    SELECT
      pmd.project_id,
      pmd.sample_date,
      dm.metric_group,
      SUM(tm.amount) AS amount,
      COUNT(DISTINCT CASE WHEN tm.amount > 0 THEN tm.sample_date END) AS active_days
    FROM project_measurement_dates AS pmd
    JOIN oso.timeseries_metrics_by_project_v0 AS tm
      ON tm.project_id = pmd.project_id
     AND tm.sample_date BETWEEN pmd.measurement_date - INTERVAL '179' DAY
                            AND pmd.measurement_date
    JOIN daily_metrics AS dm
      ON tm.metric_id = dm.metric_id
    GROUP BY 1, 2, 3
  ),

  -- Pivot the metrics
  pivoted AS (
    SELECT
      project_id,
      sample_date,
      -- TODO: replace this with "internal_transactions_daily"
      COALESCE(MAX(CASE WHEN metric_group = 'contract_invocations' THEN amount END), 0) AS transaction_count,
      COALESCE(MAX(CASE WHEN metric_group = 'contract_invocations' THEN active_days END), 0) AS active_days
    FROM project_metrics
    GROUP BY project_id, sample_date
    ORDER BY project_id, sample_date
  )

SELECT
  project_id,
  sample_date,
  transaction_count,
  active_days,
  (
    transaction_count >= @transactions_threshold
    AND active_days >= @days_with_onchain_activity_threshold
  ) AS meets_all_criteria
FROM pivoted
