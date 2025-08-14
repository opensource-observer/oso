MODEL (
  name oso.int_superchain_s7_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S7 onchain builder round",
  dialect trino,
  kind full,
  grain (sample_date, project_id),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  enabled false,
);

@DEF(transactions_threshold, 1000);
@DEF(gas_fees_threshold, 0.0);
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
        (DATE('2025-02-28')),
        (DATE('2025-03-31')),
        (DATE('2025-04-30')),
        (DATE('2025-05-31')),
        (DATE('2025-06-30')),
        (DATE('2025-07-31'))
      ) AS t(measurement_date)
    )
  ),

  -- Get the daily metric IDs for the Superchain
  daily_metrics AS (
    SELECT
      m.metric_id,
      CASE 
        WHEN m.metric_name LIKE '%_contract_invocations_daily' THEN 'contract_invocations'
        WHEN m.metric_name LIKE '%_gas_fees_daily' THEN 'gas_fees'
      END AS metric_group
    FROM oso.metrics_v0 AS m
    JOIN oso.int_superchain_chain_names AS c
      ON m.metric_name LIKE CONCAT(c.chain, '_%_daily')
    WHERE m.metric_name LIKE '%_contract_invocations_daily'
       OR m.metric_name LIKE '%_gas_fees_daily'
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
      COALESCE(MAX(CASE WHEN metric_group = 'contract_invocations' THEN amount END), 0) AS transaction_count,
      COALESCE(MAX(CASE WHEN metric_group = 'gas_fees' THEN amount END), 0) AS gas_fees,
      COALESCE(MAX(CASE WHEN metric_group = 'contract_invocations' THEN active_days END), 0) AS active_days
    FROM project_metrics
    GROUP BY project_id, sample_date
    ORDER BY project_id, sample_date
  )

SELECT
  project_id,
  sample_date,
  transaction_count,
  gas_fees,
  active_days,
  (
    transaction_count >= @transactions_threshold
    AND active_days >= @days_with_onchain_activity_threshold
    AND gas_fees >= @gas_fees_threshold
  ) AS meets_all_criteria
FROM pivoted
