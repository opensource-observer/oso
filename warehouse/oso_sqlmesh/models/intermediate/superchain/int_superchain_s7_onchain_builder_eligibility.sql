/* TODO: turn this into a rolling model that includes a sample date (eg, every week) */
MODEL (
  name oso.int_superchain_s7_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S7 onchain builder round",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id)
);

@DEF(measurement_date, DATE('2025-03-01'));
@DEF(lookback_days, 180);
@DEF(transactions_threshold, 1000);
@DEF(gas_fees_threshold, 0.0);
@DEF(active_addresses_threshold, 420);
@DEF(days_with_onchain_activity_threshold, 10);

WITH builder_metrics AS (
  SELECT
    e.project_id,
    COUNT(DISTINCT e.transaction_hash) AS transaction_count,
    COUNT(DISTINCT e.from_artifact_id) AS active_addresses_count,
    COUNT(DISTINCT DATE_TRUNC('DAY', e.time)) AS active_days,
    SUM(e.gas_fee) AS gas_fees
  FROM oso.int_superchain_events_by_project AS e
  INNER JOIN oso.projects_by_collection_v1 AS pbc
    ON e.project_id = pbc.project_id
  WHERE
    e.time BETWEEN @measurement_date - INTERVAL @lookback_days DAY
      AND @measurement_date
    AND pbc.collection_name = '8-1'
    AND e.event_type IN ('CONTRACT_INVOCATION', 'CONTRACT_INTERNAL_INVOCATION')
  GROUP BY
    e.project_id
),

project_eligibility AS (
  SELECT
    project_id,
    (
      transaction_count >= @transactions_threshold
      AND active_addresses_count >= @active_addresses_threshold
      AND active_days >= @days_with_onchain_activity_threshold
      AND gas_fees >= @gas_fees_threshold
    ) AS is_eligible
  FROM builder_metrics
)
SELECT
  @measurement_date AS sample_date,
  builder_metrics.project_id,
  builder_metrics.transaction_count,
  builder_metrics.gas_fees,
  builder_metrics.active_addresses_count,
  builder_metrics.active_days,
  project_eligibility.is_eligible
FROM builder_metrics
INNER JOIN project_eligibility
  ON builder_metrics.project_id = project_eligibility.project_id