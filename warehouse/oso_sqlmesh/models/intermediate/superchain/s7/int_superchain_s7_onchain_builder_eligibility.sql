MODEL (
  name oso.int_superchain_s7_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S7 onchain builder round",
  dialect trino,
  kind full,
  grain (sample_date, project_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(transactions_threshold, 1000);
@DEF(gas_fees_threshold, 0.0);
@DEF(active_addresses_threshold, 420);
@DEF(days_with_onchain_activity_threshold, 10);
@DEF(start_date, DATE('2025-02-01'));
@DEF(end_date, DATE('2025-07-31'));

WITH
  -- get the three relevant biannual metric IDs for the Superchain
  metric_names AS (
    SELECT
      t.metric_group,
      CONCAT(c.chain, '_', t.metric_group, '_biannually') AS metric_name
    FROM (VALUES 
      ('contract_invocations'),
      ('gas_fees'),
      ('active_addresses_aggregation')
    ) AS t(metric_group)
    CROSS JOIN oso.int_superchain_chain_names AS c
  ),

  metrics AS (
    SELECT
      m.metric_id,
      mn.metric_group
    FROM oso.metrics_v0 AS m
    JOIN metric_names AS mn
      ON m.metric_name = mn.metric_name
  ),

  -- sum the binannual metrics for each project
  biannual AS (
    SELECT
      tm.project_id,
      m.metric_group,
      tm.sample_date,
      SUM(tm.amount) AS amount
    FROM oso.timeseries_metrics_by_project_v0 AS tm
    JOIN metrics AS m
      ON tm.metric_id = m.metric_id
    WHERE tm.sample_date BETWEEN @start_date AND @end_date
    GROUP BY 1,2,3
  ),

  -- use daily invocations to derive active_days
  daily_metrics AS (
    SELECT
      m.metric_id
    FROM oso.metrics_v0 AS m
    JOIN oso.int_superchain_chain_names AS c
      ON m.metric_name = CONCAT(c.chain, '_contract_invocations_daily')
  ),

  -- enumerate each window end (project + date)
  active_windows AS (
    SELECT DISTINCT
      project_id,
      sample_date
    FROM biannual
  ),

  -- count distinct “active” days in the prior 180 days
  active_days_calc AS (
    SELECT
      aw.project_id,
      'active_days' AS metric_group,
      aw.sample_date,
      COUNT(DISTINCT tm.sample_date) FILTER (WHERE tm.amount > 0) AS amount
    FROM active_windows AS aw
    JOIN oso.timeseries_metrics_by_project_v0 AS tm
      ON tm.project_id = aw.project_id
     AND tm.sample_date BETWEEN aw.sample_date - INTERVAL '179' DAY
                            AND aw.sample_date
    JOIN daily_metrics AS dm
      ON tm.metric_id = dm.metric_id
    GROUP BY 1,2,3
  ),

  -- stack them back together
  all_metrics AS (
    SELECT * FROM biannual
    UNION ALL
    SELECT * FROM active_days_calc
  ),

  -- pivot
  pivoted AS (
    SELECT
      project_id,
      sample_date,
      COALESCE(MAX(CASE WHEN metric_group = 'contract_invocations'           THEN amount END), 0) AS transaction_count,
      COALESCE(MAX(CASE WHEN metric_group = 'gas_fees'                       THEN amount END), 0) AS gas_fees,
      COALESCE(MAX(CASE WHEN metric_group = 'active_addresses_aggregation'   THEN amount END), 0) AS active_addresses_count,
      COALESCE(MAX(CASE WHEN metric_group = 'active_days'                    THEN amount END), 0) AS active_days
    FROM all_metrics
    GROUP BY project_id, sample_date
    ORDER BY project_id, sample_date
  )

SELECT
  project_id,
  sample_date,
  transaction_count,
  gas_fees,
  active_addresses_count,
  active_days,
  (
    CAST(transaction_count >= @transactions_threshold AS INTEGER) +
    CAST(active_days >= @days_with_onchain_activity_threshold AS INTEGER) +
    CAST(active_addresses_count >= @active_addresses_threshold AS INTEGER) +
    CAST(gas_fees >= @gas_fees_threshold AS INTEGER)
     >= 3
   ) AS meets_all_criteria
FROM pivoted